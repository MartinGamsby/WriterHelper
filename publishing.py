# Social publishing, split in two phases so the UI can show a confirmation
# popup: prepare_post() computes what WOULD be sent (no side effects),
# publish() actually sends it. No Qt.
import os
import webbrowser

import rendering
import thread_split


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


PLATFORMS = {
    "bluesky": Platform("bluesky", "Bluesky", "Bluesky", 300, _make_bsky),
    "x": Platform("x", "X / Twitter", "X/Twitter", 280, _make_x),
}


# ========================================================================================
def image_filename(article):
    """Page 1 of the captured card — what the image fallback attaches."""
    return f"richTextArea_{article.hl}1.png"


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
    return {
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
        # An article must carry at least one facet (it drives which site "door" the
        # post appears under). Pair-shared, so either language reflects the pair.
        "facets_ok": bool(article.facets),
    }


# ========================================================================================
def publish(article, platform_key, mode, message, options=None) -> dict:
    """Actually post. `mode` is "text" (message only), "image" (message + page-1
    PNG), or "thread" (a reply chain split on `---` lines). `message` is the
    user-confirmed text from the popup. `options` carries thread choices:
    `{"number": bool, "image": bool}`."""
    p = PLATFORMS[platform_key]

    if not article.facets:
        return {"ok": False, "url": "",
                "error": "Add at least one facet before publishing "
                         "(facets drive the site's doors)."}

    existing = article.get_link(p.link_name)
    if existing:
        return {"ok": False, "url": existing,
                "error": "A %s link already exists. Clear it to re-post." % p.label}

    if mode == "thread":
        return _publish_thread(article, p, message, options or {})

    if mode == "image":
        img = image_filename(article)
        if not os.path.isfile(img):
            return {"ok": False, "url": "",
                    "error": "%s not found — Grab the image card first." % img}
        alt_text = rendering.plain_text(article)
        url = p.make_poster(article.hl).post(msg=message, image_local_url=img,
                                             alt_text=alt_text)
    else:
        if len(message) > p.max_length:
            return {"ok": False, "url": "",
                    "error": "Text is %d characters; %s allows %d."
                             % (len(message), p.label, p.max_length)}
        url = p.make_poster(article.hl).post(msg=message, image_local_url=None,
                                             alt_text=message)

    article.set_link(p.link_name, url)
    webbrowser.open(url)
    return {"ok": True, "url": url, "error": ""}


# ========================================================================================
def _publish_thread(article, p, message, opts) -> dict:
    """Post `message` (segments separated by `---` lines) as a reply chain. The
    first post's URL is stored in the link slot (the idempotence guard for the
    whole thread)."""
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
    if opts.get("image"):
        img = image_filename(article)
        if not os.path.isfile(img):
            return {"ok": False, "url": "",
                    "error": "%s not found — Grab the image card first." % img}
        image = img

    alt_text = rendering.plain_text(article)
    urls = p.make_poster(article.hl).post_thread(messages=segments,
                                                 image_local_url=image,
                                                 alt_text=alt_text)
    if not urls:
        return {"ok": False, "url": "", "error": "Thread post failed."}

    article.set_link(p.link_name, urls[0])
    webbrowser.open(urls[0])
    return {"ok": True, "url": urls[0], "urls": urls, "error": ""}
