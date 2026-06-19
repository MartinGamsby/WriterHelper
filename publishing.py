# Social publishing, split in two phases so the UI can show a confirmation
# popup: prepare_post() computes what WOULD be sent (no side effects),
# publish() actually sends it. No Qt.
import os
import re
import sys
import traceback
import webbrowser

import localize
import rendering
import site_push
import thread_split

# Bluesky is the only platform we hand an explicit link-preview card to (X/Facebook
# unfurl the URL in the post text themselves). A bare http(s) URL, for scanning the
# message when no YouTube slot is set.
_MSG_URL_RE = re.compile(r'https?://[^\s<>"\']+')
# Link slots that hold a video URL worth turning into a Bluesky link card, preferred
# over any URL found in the message text.
_EMBED_LINK_SLOTS = ("YouTube", "YouTube Shorts")


# ========================================================================================
class Platform:
    def __init__(self, key, label, link_name, max_length, make_poster):
        self.key = key
        self.label = label
        self.link_name = link_name      # the Link slot used as idempotence guard
        self.max_length = max_length
        self.make_poster = make_poster  # callable(hl) -> Post adapter


# ========================================================================================
def _make_bsky(hl):
    from post_bsky import PostBsky
    return PostBsky(hl)


def _make_x(hl):
    from post_x import PostX
    return PostX(hl)


def _make_fb(hl):
    from post_fb import PostFB
    return PostFB(hl)


def _make_ig(hl):
    from post_ig import PostIG
    return PostIG(hl)


PLATFORMS = {
    "bluesky": Platform("bluesky", "Bluesky", "Bluesky", 300, _make_bsky),
    "x": Platform("x", "X / Twitter", "X/Twitter", 280, _make_x),
    # Facebook posts allow ~63k chars, so a post always "fits" as text (thread mode
    # is offered by the popup but PostFB has no post_thread — text/image only).
    "facebook": Platform("facebook", "Facebook", "Facebook", 63206, _make_fb),
    # Instagram is image-only and image-must-be-public: it's a two-step flow
    # (stage_instagram_image, then publish) — 2200 is IG's caption limit.
    # See [[instagram-adapter]].
    "instagram": Platform("instagram", "Instagram", "Instagram", 2200, _make_ig),
}


# ========================================================================================
def capture_filename(article, page):
    """The captured card file for `page` (1-indexed). Named by the article's
    **slug** (+ hl) so a capture is tied to the article it was grabbed for: the
    publish/commit step resolves the CURRENT article's slug, so a stale grab from a
    different article simply isn't found (and editing the title changes the slug, so
    an out-of-date grab no longer matches). JPEG, so it doubles as the Instagram
    asset ([[instagram-adapter]])."""
    return f"richTextArea_{article.get_slug()}_{article.hl}{page}.jpg"


def image_filename(article):
    """Page 1 of the captured card — what image mode attaches / IG commits."""
    return capture_filename(article, 1)


# ========================================================================================
def _ig_image_dest(article):
    """The IG source image's filename inside the site repo (slug + hl, JPEG)."""
    return "%s.%s.jpg" % (article.get_slug(), article.hl)


def stage_instagram_image(article) -> dict:
    """Step 1 of an Instagram post: copy the grabbed card into the site repo and
    git-push it so a public URL exists (IG fetches the image server-side, so it must be
    reachable BEFORE the post). Returns site_push's `{ok, public_url, log, error}`; the
    public_url is handed back to `publish(... mode="image", {"image_url": url})`.
    See [[instagram-adapter]]."""
    img = image_filename(article)
    if not os.path.isfile(img):
        return {"ok": False, "public_url": "", "log": [],
                "error": "%s not found — use Square, then Grab the image card first." % img}
    repo = localize.find_repo_root(article.get_posts_folder())
    if not repo:
        return {"ok": False, "public_url": "", "log": [],
                "error": "Couldn't locate the martingamsby.com checkout above %s."
                         % article.get_posts_folder()}
    commit_msg = "IG image: %s (%s)" % (article.get_slug(), article.hl)
    return site_push.stage_and_push_image(repo, img, _ig_image_dest(article), commit_msg)


# ========================================================================================
def embed_candidate(article, message=""):
    """The URL a Bluesky link-preview card would point at, or "". A YouTube link slot
    wins (the operator set it deliberately, and Bluesky renders it as a video card);
    otherwise the first URL in `message` (so a link pasted into the post is unfurled)."""
    for slot in _EMBED_LINK_SLOTS:
        url = article.get_link(slot)
        if url:
            return url
    m = _MSG_URL_RE.search(message or "")
    return m.group(0).rstrip('.,;:!?)]}\'"') if m else ""


# ========================================================================================
def prepare_post(article, platform_key) -> dict:
    """Everything the confirmation popup needs. Performs NO side effects."""
    p = PLATFORMS[platform_key]
    text = rendering.plain_text(article)
    fits = len(text) <= p.max_length
    img = image_filename(article)
    img_exists = os.path.isfile(img)
    # The auto-split is what seeds the editable thread textarea. Segments are left
    # un-numbered (counters are stamped at publish) but split with room reserved for
    # them, so turning numbering on never pushes a segment over the limit.
    segments = thread_split.split_text(text, p.max_length, number=True)
    info = {
        "platform": p.key,
        "label": p.label,
        "max_length": p.max_length,
        "existing_url": article.get_link(p.link_name),
        "text": text,
        "text_length": len(text),
        "fits": fits,
        # A post that doesn't fit is best served as a thread; image stays available.
        "suggested_mode": "text" if fits else "thread",
        "thread_text": thread_split.join_for_edit(segments),
        "thread_count": len(segments),
        "separator": thread_split.SEPARATOR,
        # A loose identity label for the preview cards (not the real platform handle).
        "author": "MartinGamsby.com/%s" % article.hl,
        "title": article.title,
        "image_file": img,
        "image_exists": img_exists,
        "image_data_url": rendering.data_url(img) if img_exists else "",
        # The article's own header image, the default attachment for a thread (so a
        # thread shows the real picture, not the whole text rendered onto a card).
        "article_image_exists": bool(rendering.excerpt_image_file(article)),
        "article_image_data_url": rendering.excerpt_image_local(article)
        if article.excerpt_image else "",
        # An article must carry at least one facet (it drives which site "door" the
        # post appears under). Pair-shared, so either language reflects the pair.
        "facets_ok": bool(article.facets),
        # Bluesky-only: the URL an optional link-preview card would embed (a YouTube
        # slot, else a URL in the text). The popup shows a checkbox when this is set.
        "embed_url": embed_candidate(article, text) if p.key == "bluesky" else "",
    }
    if p.key == "instagram":
        # The IG popup needs to know it can locate the site repo (step 1 = push the image
        # there), what the pushed file will be called, and whether that image is ALREADY
        # pushed — so reopening the popup skips straight to publish instead of forcing a
        # redundant re-push. `text` is the default caption; `image_*` (the grabbed card)
        # is the required, only attachable image.
        repo = localize.find_repo_root(article.get_posts_folder())
        info["ig_repo_found"] = bool(repo)
        info["ig_image_dest"] = _ig_image_dest(article)
        status = (site_push.image_status(repo, _ig_image_dest(article), img)
                  if repo and img_exists else {"pushed": False, "public_url": ""})
        info["ig_image_pushed"] = status["pushed"]
        info["ig_public_url"] = status["public_url"]
        # The image ACTUALLY sitting in the repo (what Instagram will fetch), as a data
        # URL — so the popup can show it next to the current card and the operator can
        # catch a stale/changed image. "" when nothing is staged for this post yet.
        dest_abs = (os.path.join(repo, site_push.IG_ASSET_SUBDIR, _ig_image_dest(article))
                    if repo else "")
        info["ig_repo_image_data_url"] = (rendering.data_url(dest_abs)
                                          if dest_abs and os.path.isfile(dest_abs) else "")
    return info


# ========================================================================================
def _log_post_exc(p, exc):
    """Log a posting failure with full stack + the platform's structured error so the
    real cause is visible in the console (the UI only gets the short message)."""
    print("[publish] %s post failed: %r" % (p.label, exc), file=sys.stderr)
    # tweepy.HTTPException carries parsed API errors and the raw HTTP response body.
    for attr in ("api_codes", "api_messages", "api_errors"):
        val = getattr(exc, attr, None)
        if val:
            print("[publish]   %s: %s" % (attr, val), file=sys.stderr)
    resp = getattr(exc, "response", None)
    if resp is not None:
        try:
            print("[publish]   HTTP %s: %s" % (resp.status_code, resp.text),
                  file=sys.stderr)
        except Exception:
            pass
    traceback.print_exc()


# ========================================================================================
def _post_error(p, exc) -> str:
    """Turn a platform adapter exception into a short, actionable popup message."""
    msg = str(exc).strip()
    # X/Twitter's generic 403 when the developer App isn't attached to a Project or
    # the Access Token lacks write scope. The raw message is a wall of text; give the
    # operator the concrete fix instead.
    if "attached to a Project" in msg or "developer App" in msg:
        return ("%s refused the post (403): the X developer App must be attached to a "
                "Project and the Access Token must have Read+Write scope. Enable write, "
                "regenerate the Access Token & Secret, then update settings_x_<hl>.ini."
                % p.label)
    return "%s couldn't post: %s" % (p.label, msg)


# ========================================================================================
def _resolve_image(article, source):
    """Local file path for an attachment, or `(None, error)`. `source` is
    `"grabbed"` (the captured text-card PNG) or `"article"` (the post's own header
    image, already self-hosted to a local file on save)."""
    if source == "grabbed":
        img = image_filename(article)
        if not os.path.isfile(img):
            return None, "%s not found — Grab the image card first." % img
        return img, None
    if source == "article":
        path = rendering.excerpt_image_file(article)
        if path:
            return path, None
        return None, ("This article has no local image to attach "
                      "(set one, or pick the grabbed text card).")
    return None, "Unknown image source: %r" % source


# ========================================================================================
def publish(article, platform_key, mode, message, options=None) -> dict:
    """Actually post. `mode` is "text" (message only), "image" (message + page-1
    PNG), or "thread" (a reply chain split on `---` lines). `message` is the
    user-confirmed text from the popup. `options` carries thread choices and the embed
    flag: `{"number": bool, "image": "none"|"grabbed"|"article", "embed": bool}`."""
    p = PLATFORMS[platform_key]
    opts = options or {}

    if not article.facets:
        return {"ok": False, "url": "",
                "error": "Add at least one facet before publishing "
                         "(facets drive the site's doors)."}

    existing = article.get_link(p.link_name)
    if existing:
        return {"ok": False, "url": existing,
                "error": "A %s link already exists. Clear it to re-post." % p.label}

    # Instagram is image-only and needs its image already public (step 1); it carries no
    # text/thread modes and no link card, so it gets its own short path.
    if p.key == "instagram":
        return _publish_instagram(article, p, message, opts)

    # Optional Bluesky link-preview card (None = plain post, as before).
    embed_url = (embed_candidate(article, message)
                 if opts.get("embed") and p.key == "bluesky" else None) or None

    if mode == "thread":
        return _publish_thread(article, p, message, opts, embed_url)

    if mode == "image":
        # Default to the grabbed text card (the historical image-mode attachment); the
        # popup can also pick the article's own header image.
        source = opts.get("image", "grabbed")
        img, error = _resolve_image(article, source)
        if error:
            return {"ok": False, "url": "", "error": error}
        # The grabbed card carries the whole article as text, so its alt is the full
        # plain text; the article header image is decorative, so use the title.
        alt_text = rendering.plain_text(article) if source == "grabbed" else article.title
        # An attached image owns the post's embed slot, so no link card here.
        send = lambda: p.make_poster(article.hl).post(
            msg=message, image_local_url=img, alt_text=alt_text)
    else:
        if len(message) > p.max_length:
            return {"ok": False, "url": "",
                    "error": "Text is %d characters; %s allows %d."
                             % (len(message), p.label, p.max_length)}
        send = lambda: p.make_poster(article.hl).post(
            msg=message, image_local_url=None, alt_text=message, embed_url=embed_url)

    try:
        url = send()
    except Exception as exc:  # auth/network failure must reach the UI, not just the console
        _log_post_exc(p, exc)
        return {"ok": False, "url": "", "error": _post_error(p, exc)}

    article.set_link(p.link_name, url)
    webbrowser.open(url)
    return {"ok": True, "url": url, "error": ""}


# ========================================================================================
def _publish_instagram(article, p, caption, opts) -> dict:
    """Post the (already-public) image + caption to Instagram. The public image URL
    comes from the prior stage_instagram_image step, handed back in
    `opts["image_url"]`. IG is image-only, so `caption` is the whole text."""
    image_url = opts.get("image_url")
    if not image_url:
        return {"ok": False, "url": "",
                "error": "Push the Instagram image to the site first (step 1)."}
    if len(caption) > p.max_length:
        return {"ok": False, "url": "",
                "error": "Caption is %d characters; %s allows %d."
                         % (len(caption), p.label, p.max_length)}
    try:
        url = p.make_poster(article.hl).post(msg=caption, image_url=image_url,
                                             alt_text=caption)
    except Exception as exc:  # auth/network failure must reach the UI, not just the console
        _log_post_exc(p, exc)
        return {"ok": False, "url": "", "error": _post_error(p, exc)}

    article.set_link(p.link_name, url)
    webbrowser.open(url)
    return {"ok": True, "url": url, "error": ""}


# ========================================================================================
def _publish_thread(article, p, message, opts, embed_url=None) -> dict:
    """Post `message` (segments separated by `---` lines) as a reply chain. The
    first post's URL is stored in the link slot (the idempotence guard for the
    whole thread). `embed_url` (if any) adds a link card to the first post."""
    segments = thread_split.split_on_separator(message)
    if not segments:
        return {"ok": False, "url": "", "error": "Nothing to post."}

    if opts.get("number", True):
        segments = thread_split.number_segments(segments)

    over = [i + 1 for i, s in enumerate(segments) if len(s) > p.max_length]
    if over:
        return {"ok": False, "url": "",
                "error": "Post %s over the %d-character limit."
                         % (", ".join(map(str, over)), p.max_length)}

    image = None
    source = opts.get("image", "none")
    if source and source != "none":
        image, error = _resolve_image(article, source)
        if error:
            return {"ok": False, "url": "", "error": error}

    # Alt text: the grabbed card carries the whole article as text, so its alt is the
    # full plain text; the article header image is decorative, so use the title.
    alt_text = rendering.plain_text(article) if source == "grabbed" else article.title
    try:
        urls = p.make_poster(article.hl).post_thread(messages=segments,
                                                     image_local_url=image,
                                                     alt_text=alt_text,
                                                     embed_url=embed_url)
    except Exception as exc:  # auth/network failure must reach the UI, not just the console
        _log_post_exc(p, exc)
        return {"ok": False, "url": "", "error": _post_error(p, exc)}
    if not urls:
        return {"ok": False, "url": "", "error": "Thread post failed."}

    article.set_link(p.link_name, urls[0])
    webbrowser.open(urls[0])
    return {"ok": True, "url": urls[0], "urls": urls, "error": ""}
