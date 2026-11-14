# Social publishing, split in two phases so the UI can show a confirmation
# popup: prepare_post() computes what WOULD be sent (no side effects),
# publish() actually sends it — through a native adapter (transport "api") or by
# queueing a job for Claude in Chrome (transport "browser", [[browser-hook]]).
# The registry lives in platforms.py. No Qt.
import os
import re
import sys
import traceback
import webbrowser

import browser_jobs
import instagram_flow
import publish_config
import rendering
import thread_split
from platforms import PLATFORMS, Platform  # noqa: F401  (re-exported for callers/tests)

# Bluesky is the only platform we hand an explicit link-preview card to (the others
# unfurl the URL in the post text themselves). A bare http(s) URL, for scanning the
# message when no YouTube slot is set.
_MSG_URL_RE = re.compile(r'https?://[^\s<>"\']+')
# Link slots that hold a video URL worth turning into a Bluesky link card, preferred
# over any URL found in the message text.
_EMBED_LINK_SLOTS = ("YouTube", "YouTube Shorts")


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
def stage_instagram_image(article) -> dict:
    """Instagram-over-API step 1 (push the grabbed card so it has a public URL). See
    instagram_flow / [[instagram-adapter]]."""
    return instagram_flow.stage_image(article, image_filename(article))


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
def _suggested_mode(p, fits):
    # An image-required platform is always image mode. Else: a post that doesn't fit is
    # best served as a thread where one can be posted, otherwise as an image (the whole
    # card as a picture).
    if p.media == "image":
        return "image"
    if fits:
        return "text"
    return "thread" if p.supports_thread else "image"


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
    transport = p.transport
    info = {
        "platform": p.key,
        "label": p.label,
        "max_length": p.max_length,
        "existing_url": article.get_link(p.link_name),
        "text": text,
        "text_length": len(text),
        "fits": fits,
        "suggested_mode": _suggested_mode(p, fits),
        # Lets the popup hide the Thread radio where no reply chain can be posted.
        "supports_thread": p.supports_thread,
        # The media the platform requires: "any" | "image" | "video". The popup offers
        # only valid modes (image-only platforms) or gates entirely (video, which
        # WriterHelper can't author). See [[social-publishing]].
        "media": p.media,
        # "api" (posts now) or "browser" (queued for Claude in Chrome, [[browser-hook]]).
        "transport": transport,
        "via": p.via,
        "compose_url": p.browser_url,
        # A queued-but-unreported browser job for this post: the popup shows its status
        # instead of a composer (the double-post guard while Claude is still working).
        "pending_job": (browser_jobs.pending_for(article, p)
                        if transport == "browser" else None),
        "hook_command": publish_config.hook_command() if transport == "browser" else "",
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
    if p.key == "instagram" and transport == "api":
        info.update(instagram_flow.prepare_extras(article, img, img_exists))
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
    `"grabbed"` (the captured text-card JPEG) or `"article"` (the post's own header
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
def _failure(p, exc) -> dict:
    _log_post_exc(p, exc)
    return {"ok": False, "url": "", "error": _post_error(p, exc)}


def _plan(article, p, mode, message, opts):
    """What a confirmed post consists of, independent of HOW it's sent:
    `(posts, image, alt_text, error)` — `posts` is one message, or a thread's segments;
    `image` is a local file attached to the first post (or None)."""
    if mode == "thread":
        if not p.supports_thread:
            return None, None, "", "%s doesn't support threads." % p.label
        posts = thread_split.split_on_separator(message)
        if not posts:
            return None, None, "", "Nothing to post."
        if opts.get("number", True):
            posts = thread_split.number_segments(posts)
        over = [i + 1 for i, s in enumerate(posts) if len(s) > p.max_length]
        if over:
            return None, None, "", ("Post %s over the %d-character limit."
                                    % (", ".join(map(str, over)), p.max_length))
        source = opts.get("image", "none")
    elif mode == "image":
        posts = [message]
        # Default to the grabbed text card (the historical image-mode attachment); the
        # popup can also pick the article's own header image.
        source = opts.get("image", "grabbed")
    else:
        if not message.strip():
            return None, None, "", "Nothing to post."
        posts = [message]
        source = "none"
    if mode != "thread" and len(message) > p.max_length:
        return None, None, "", ("Text is %d characters; %s allows %d."
                                % (len(message), p.label, p.max_length))

    image = None
    if source and source != "none":
        image, error = _resolve_image(article, source)
        if error:
            return None, None, "", error
    # The grabbed card carries the whole article as text, so its alt is the full plain
    # text; the article header image is decorative, so use the title.
    alt_text = (rendering.plain_text(article) if source == "grabbed"
                else message if mode == "text" else article.title)
    return posts, image, alt_text, None


def publish(article, platform_key, mode, message, options=None) -> dict:
    """Actually post (or queue for Claude in Chrome). `mode` is "text" (message only),
    "image" (message + an image) or "thread" (a reply chain split on `---` lines).
    `message` is the user-confirmed text from the popup. `options`:
    `{"number": bool, "image": "none"|"grabbed"|"article", "embed": bool,
    "image_url": str}` (image_url: Instagram-over-API only)."""
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

    transport = p.transport
    if transport == "browser" and browser_jobs.pending_for(article, p):
        return {"ok": False, "url": "",
                "error": "A %s post is already queued for Claude in Chrome — wait for it "
                         "or cancel it first." % p.label}

    # A video-only platform can't be served: WriterHelper authors text + image cards,
    # never video. Gate it here too (the popup also blocks it).
    if p.media == "video":
        return {"ok": False, "url": "",
                "error": "%s posts require a video; WriterHelper produces text and image "
                         "cards only. Post there by hand and paste the URL." % p.label}

    # Instagram over the Graph API needs its image already public (step 1); it gets its
    # own short path. Over the browser it's an ordinary image post.
    if p.key == "instagram" and transport == "api":
        return instagram_flow.publish(article, p, message, opts, _failure)

    if p.media == "image" and mode != "image":
        return {"ok": False, "url": "",
                "error": "%s requires an image — use Title + image mode." % p.label}

    posts, image, alt_text, error = _plan(article, p, mode, message, opts)
    if error:
        return {"ok": False, "url": "", "error": error}

    if transport == "browser":
        job = browser_jobs.create(article, p, mode, posts, image or "", alt_text)
        return {"ok": True, "queued": True, "url": "", "job": job,
                "hook": browser_jobs.run_hook(job), "error": ""}

    # Optional Bluesky link-preview card (None = plain post). An attached image owns the
    # post's embed slot, so no card in image mode.
    embed_url = (embed_candidate(article, message)
                 if opts.get("embed") and p.key == "bluesky" and mode != "image"
                 else None) or None
    try:
        poster = p.make_poster(article.hl)
        if mode == "thread":
            urls = poster.post_thread(messages=posts, image_local_url=image,
                                      alt_text=alt_text, embed_url=embed_url)
        elif mode == "image":
            urls = [poster.post(msg=message, image_local_url=image, alt_text=alt_text)]
        else:
            urls = [poster.post(msg=message, image_local_url=None, alt_text=message,
                                embed_url=embed_url)]
    except Exception as exc:  # auth/network failure must reach the UI, not just the console
        return _failure(p, exc)
    if not urls or not urls[0]:
        return {"ok": False, "url": "", "error": "%s post failed." % p.label}

    # The first post's URL is the slot guard (for a thread: the whole chain's).
    article.set_link(p.link_name, urls[0])
    webbrowser.open(urls[0])
    result = {"ok": True, "url": urls[0], "error": ""}
    if mode == "thread":
        result["urls"] = urls
    return result
