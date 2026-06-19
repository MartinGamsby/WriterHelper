# post-bridge.com adapter — one API key fans a post out to LinkedIn, Threads,
# Pinterest, TikTok, … without per-platform developer apps / tokens. Inherits the
# Post base (msg/image/alt contract) so publishing.py drives it exactly like the
# native Bluesky/X/Facebook adapters. No Qt. See [[post-bridge-adapter]].
#
# Flow (official API, confirmed from the post-bridge-api npm client):
#   1. resolve the target social_account id(s) for (platform, hl)
#   2. if an image is attached: POST /v1/media/create-upload-url -> PUT the bytes
#      to the returned signed URL -> media_id   (LOCAL upload — no public-URL hack)
#   3. POST /v1/posts {caption, social_accounts, media} (no scheduled_at = instant)
#   4. poll GET /v1/post-results?post_id= until the per-platform public URL appears
#      (it's produced asynchronously) — that URL feeds the Link slot.
import configparser
import os
import time

import requests

from post import Post

BASE_URL = "https://api.post-bridge.com"
CONFIG_FILE = "settings_postbridge.ini"      # ONE key, shared across platforms + hl
_TIMEOUT = 30                                # per-request seconds
# The per-platform URL is minted asynchronously after the post is accepted; an instant
# text/image post resolves in a few seconds. Poll a bounded number of times, then fall
# back to the manual-link instruction (same convention as post_ig's permalink fallback).
_RESULT_POLLS = 8
_RESULT_DELAY = 2                            # seconds between polls

# Map an image extension to the upload's allowed MIME enum (image/png|image/jpeg). The
# grabbed card is always JPEG; the article header image may be PNG. Anything else is
# rejected with a clear message rather than guessing.
_MIME_BY_EXT = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}

# post-bridge labels X as "x"; accept the legacy alias so callers can say "twitter".
_PLATFORM_ALIASES = {"twitter": "x"}


# ====================================================================================
class PostBridgeError(RuntimeError):
    """A post-bridge API failure, already shaped into an operator-facing message."""


# ====================================================================================
class PostBridge(Post):
    """One post-bridge platform target (e.g. "linkedin"). `platform` is the
    post-bridge platform string; `hl` selects the language so per-language accounts
    can be pinned in the INI. post_thread is intentionally NOT overridden — post-bridge
    has no native reply chain, so Thread mode raises NotImplementedError (Text/Image
    modes are the supported shapes)."""

    # ====================================================================================
    def __init__(self, hl, platform):
        self.platform = _PLATFORM_ALIASES.get(platform.lower(), platform.lower())
        # A single [Accounts] section pins account ids per platform/language (optional);
        # seed it so a fresh template writes both sections.
        self._accounts_seed = {}
        Post.__init__(self, hl, access={"ApiKey": "<TODO>"})

    # The base __init__ prints get_handle(); post-bridge has no per-adapter handle.
    def get_handle(self):
        return "post-bridge:%s" % self.platform

    def config_filename(self):
        return CONFIG_FILE

    def get_api_key(self):
        return self.config["Access"]["ApiKey"]

    # The base only seeds [Access]; add an [Accounts] section so the written template
    # documents the optional per-language pinning.
    def load_config(self):
        self.config["Accounts"] = {
            "# linkedin": "123        ; account id for any-language LinkedIn",
            "# linkedin_fr": "124     ; override for the French post button",
        }
        Post.load_config(self)

    # ====================================================================================
    def _headers(self):
        key = self.get_api_key()
        if not key or key == "<TODO>":
            raise PostBridgeError(
                "post-bridge API key is missing — put your pb_live_… key in "
                "[Access] ApiKey of %s." % CONFIG_FILE)
        return {"Authorization": "Bearer %s" % key}

    def _raise_for(self, r, what):
        """Turn a non-2xx post-bridge response into a readable PostBridgeError."""
        try:
            body = r.json()
            detail = body.get("message") or body.get("error") or body
        except ValueError:
            detail = (r.text or "").strip()[:300]
        raise PostBridgeError("post-bridge %s failed (HTTP %s): %s"
                              % (what, r.status_code, detail))

    # ====================================================================================
    def list_accounts(self):
        """All connected social accounts: [{id, platform, username}, …]."""
        r = requests.get(BASE_URL + "/v1/social-accounts",
                         headers=self._headers(), timeout=_TIMEOUT)
        if not r.ok:
            self._raise_for(r, "social-accounts")
        return r.json().get("data", [])

    def _configured_ids(self):
        """Account ids pinned in [Accounts] for this platform/language, or None.
        Tries the language-specific key first (`<platform>_<hl>`), then the bare
        platform key — so a single account needs no per-language line."""
        section = self.config["Accounts"] if self.config.has_section("Accounts") else {}
        for key in ("%s_%s" % (self.platform, self.hl), self.platform):
            raw = section.get(key)
            if raw:
                ids = [int(x) for x in raw.replace(";", ",").split(",")
                       if x.strip().isdigit()]
                if ids:
                    return ids
        return None

    def _resolve_account_ids(self):
        """The social_account id(s) this post targets. A pinned [Accounts] entry wins;
        otherwise auto-resolve by platform. Exactly one match → use it (the zero-config
        single-account case). Several matches with no pin → refuse and list them, so a
        bilingual post can't silently land on the wrong-language account."""
        pinned = self._configured_ids()
        if pinned:
            return pinned
        matches = [a for a in self.list_accounts()
                   if str(a.get("platform", "")).lower() == self.platform]
        if not matches:
            raise PostBridgeError(
                "No %s account is connected to post-bridge. Connect one in the "
                "post-bridge dashboard, then try again." % self.platform)
        if len(matches) == 1:
            return [int(matches[0]["id"])]
        listing = ", ".join("%s=%s (@%s)" % (m["id"], m["platform"], m.get("username", ""))
                            for m in matches)
        raise PostBridgeError(
            "Several %s accounts are connected (%s). Pin the right one per language in "
            "[Accounts] of %s, e.g. `%s_%s = <id>`."
            % (self.platform, listing, CONFIG_FILE, self.platform, self.hl))

    # ====================================================================================
    def _upload_image(self, image_local_url):
        """Upload a local image and return its media_id. Two steps: ask for a signed
        upload URL, then PUT the bytes to it (post-bridge accepts a LOCAL upload, so —
        unlike the Meta Instagram path — no public-URL staging is needed)."""
        ext = os.path.splitext(image_local_url)[1].lower()
        mime = _MIME_BY_EXT.get(ext)
        if not mime:
            raise PostBridgeError(
                "post-bridge can't upload %r — attach a JPEG or PNG." % os.path.basename(image_local_url))
        size = os.path.getsize(image_local_url)
        r = requests.post(BASE_URL + "/v1/media/create-upload-url",
                         headers=self._headers(),
                         json={"mime_type": mime, "size_bytes": size,
                               "name": os.path.basename(image_local_url)},
                         timeout=_TIMEOUT)
        if not r.ok:
            self._raise_for(r, "create-upload-url")
        payload = r.json()
        upload_url, media_id = payload.get("upload_url"), payload.get("media_id")
        if not upload_url or not media_id:
            raise PostBridgeError("create-upload-url returned no upload_url/media_id: %s"
                                  % payload)
        with open(image_local_url, "rb") as f:
            put = requests.put(upload_url, data=f.read(),
                               headers={"Content-Type": mime}, timeout=_TIMEOUT)
        if not put.ok:
            self._raise_for(put, "media upload (PUT)")
        return media_id

    # ====================================================================================
    def post(self, msg, image_local_url, alt_text, embed_url=None):
        """Create one instant post on this platform. `image_local_url` (optional) is
        uploaded and attached; `embed_url` is ignored (post-bridge platforms unfurl links
        from the caption themselves). Returns the public post URL, polling post-results
        for it; raises PostBridgeError on any API failure (publishing.py surfaces it)."""
        account_ids = self._resolve_account_ids()

        media = []
        if image_local_url and os.path.isfile(image_local_url):
            media.append(self._upload_image(image_local_url))

        body = {"caption": msg, "social_accounts": account_ids}
        if media:
            body["media"] = media
        r = requests.post(BASE_URL + "/v1/posts", headers=self._headers(),
                         json=body, timeout=_TIMEOUT)
        if not r.ok:
            self._raise_for(r, "create post")
        post_id = r.json().get("id")
        if not post_id:
            raise PostBridgeError("post-bridge created no post id: %s" % r.json())
        return self._resolve_post_url(post_id, account_ids)

    # ====================================================================================
    def _resolve_post_url(self, post_id, account_ids):
        """Poll post-results until this platform's public URL is minted. A failed
        result row is raised (with its error); a successful row with no URL yet, or no
        row at all after the polling budget, raises the manual-link instruction so the
        operator pastes the URL by hand instead of risking a blind re-post (same
        convention as post_ig's permalink fallback)."""
        wanted = set(account_ids)
        for attempt in range(_RESULT_POLLS):
            r = requests.get(BASE_URL + "/v1/post-results",
                             headers=self._headers(), params={"post_id": post_id},
                             timeout=_TIMEOUT)
            if r.ok:
                for row in r.json().get("data", []):
                    if row.get("social_account_id") not in wanted:
                        continue
                    if row.get("success") is False and row.get("error"):
                        raise PostBridgeError("%s rejected the post: %s"
                                              % (self.platform, row["error"]))
                    url = (row.get("platform_data") or {}).get("url")
                    if url:
                        return url
            if attempt < _RESULT_POLLS - 1:
                time.sleep(_RESULT_DELAY)
        raise PostBridgeError(
            "Posted to %s via post-bridge (post %s), but its public URL hasn't come back "
            "yet. Open the post-bridge dashboard, copy the post URL into the link field "
            "to avoid re-posting." % (self.platform, post_id))


# ====================================================================================
if __name__ == "__main__":
    # Read-only helper: list connected accounts so you can pin ids in [Accounts].
    bridge = PostBridge("en", "linkedin")
    try:
        for a in bridge.list_accounts():
            print("id=%s  platform=%s  @%s" % (a.get("id"), a.get("platform"),
                                               a.get("username")))
    except PostBridgeError as exc:
        print(exc)
