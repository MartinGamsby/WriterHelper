import os
import re
import sys

import requests
from bs4 import BeautifulSoup
from atproto import Client, client_utils, models
from post import Post

# A bare http(s) URL. Bluesky leaves URLs as plain (un-clickable) text unless the
# post carries link *facets*; we detect them here and build those facets.
_URL_RE = re.compile(r'https?://[^\s<>"\']+')
# YouTube watch / shorts / youtu.be / embed — captures the 11-char video id so we can
# point the link card at a reliable thumbnail without scraping.
_YOUTUBE_RE = re.compile(
    r'(?:youtube\.com/(?:watch\?v=|shorts/|embed/|live/)|youtu\.be/)([A-Za-z0-9_-]{11})')
# A browser-ish UA — some sites (YouTube included) serve thin/og-less HTML to bots.
_FETCH_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; WriterHelper link-card)"}
# Trailing characters that almost always belong to the surrounding sentence, not the
# URL (e.g. "see https://x.com/foo." or "(https://x.com/foo)"). A closing bracket is
# only trimmed when the URL has no matching opener, so Wikipedia-style "(...)" links
# survive.
_URL_TRAIL = '.,;:!?\'"'


# ====================================================================================
def _trim_url(url):
    """Strip sentence punctuation the regex greedily swallowed; return the bare URL."""
    while url:
        last = url[-1]
        if last in _URL_TRAIL:
            url = url[:-1]
        elif last in ')]}' and url.count({')': '(', ']': '[', '}': '{'}[last]) < url.count(last):
            url = url[:-1]
        else:
            break
    return url


# ====================================================================================
def build_rich_text(msg):
    """Turn `msg` into something `send_post`/`send_image` can post with clickable
    links: a `TextBuilder` carrying a link facet per URL, or the plain string
    unchanged when there are no URLs (so non-link posts behave exactly as before)."""
    pos, tb, found = 0, client_utils.TextBuilder(), False
    for m in _URL_RE.finditer(msg):
        url = _trim_url(m.group(0))
        if not url:
            continue
        if m.start() > pos:
            tb.text(msg[pos:m.start()])
        tb.link(url, url)
        pos = m.start() + len(url)
        found = True
    if not found:
        return msg
    if pos < len(msg):
        tb.text(msg[pos:])
    return tb


# ====================================================================================
def youtube_id(url):
    """The 11-char YouTube video id in `url`, or None."""
    m = _YOUTUBE_RE.search(url or "")
    return m.group(1) if m else None


# ====================================================================================
def _og(soup, prop):
    """An OpenGraph `og:<prop>` value (falling back to `name=`), or ""."""
    tag = (soup.find("meta", property="og:%s" % prop)
           or soup.find("meta", attrs={"name": "og:%s" % prop}))
    return (tag.get("content") or "").strip() if tag else ""


# ====================================================================================
def fetch_external_card(client, url):
    """Build an `app.bsky.embed.external` link-preview card for `url` from its
    OpenGraph metadata (title/description/thumbnail), uploading the thumbnail as a
    blob via the logged-in `client`. Returns the embed, or None if the page can't be
    fetched — a missing card must never block the post (caller falls back to a plain
    post). For YouTube links the thumbnail comes from img.youtube.com (reliable, no
    scraping), so Bluesky shows it as a playable video card."""
    try:
        resp = requests.get(url, timeout=10, headers=_FETCH_HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as exc:
        print("[bsky] link-card fetch failed for %s: %r" % (url, exc), file=sys.stderr)
        return None

    title = _og(soup, "title")
    if not title and soup.title and soup.title.string:
        title = soup.title.string.strip()
    description = _og(soup, "description")

    yt = youtube_id(url)
    image_url = ("https://img.youtube.com/vi/%s/hqdefault.jpg" % yt) if yt else _og(soup, "image")

    thumb = None
    if image_url:
        try:
            img = requests.get(image_url, timeout=10, headers=_FETCH_HEADERS)
            img.raise_for_status()
            thumb = client.upload_blob(img.content).blob
        except Exception as exc:
            print("[bsky] thumb upload failed for %s: %r" % (image_url, exc), file=sys.stderr)

    external = models.AppBskyEmbedExternal.External(
        uri=url, title=title or url, description=description, thumb=thumb)
    return models.AppBskyEmbedExternal.Main(external=external)


# ====================================================================================
class PostBsky(Post):

    # ====================================================================================
    def __init__(self, hl):
        Post.__init__(self, hl, access={'Handle': '<TODO>', 'AppPassword': '<TODO>'})

    # ====================================================================================
    def _post_url(self, uri):
        # uri e.g. at://did:plc:.../app.bsky.feed.post/3ls52v3vmiy2p -> the web URL.
        id = uri[uri.rfind("/") + 1:]
        return f"https://bsky.app/profile/{self.get_handle()}/post/{id}"

    # ====================================================================================
    def _send(self, client, msg, image_local_url, alt_text, reply_to, embed_url=None):
        """One post (optionally with an image, optionally a reply, optionally a link
        card). Returns the SDK response (carries .uri/.cid for building the next reply
        ref). A post's embed slot holds EITHER an image OR an external card, so an
        attached image takes precedence and `embed_url` is only honoured without one."""
        # A TextBuilder when the text has URLs (→ clickable link facets), else the
        # plain string. send_post/send_image accept either.
        text = build_rich_text(msg)
        if image_local_url and os.path.isfile(image_local_url):
            with open(image_local_url, 'rb') as f:
                return client.send_image(text=text, image=f.read(), image_alt=alt_text,
                                         langs=[self.hl], reply_to=reply_to)
        embed = fetch_external_card(client, embed_url) if embed_url else None
        return client.send_post(text, langs=[self.hl], reply_to=reply_to, embed=embed)

    # ====================================================================================
    def post(self, msg, image_local_url, alt_text, embed_url=None):
        client = Client()
        client.login(self.get_handle(), self.get_app_password())
        # More than text here: https://docs.bsky.app/docs/tutorials/creating-a-post
        post = self._send(client, msg, image_local_url, alt_text, reply_to=None,
                          embed_url=embed_url)
        return self._post_url(post.uri)

    # ====================================================================================
    def post_thread(self, messages, image_local_url, alt_text, embed_url=None):
        client = Client()
        client.login(self.get_handle(), self.get_app_password())
        urls, root, parent = [], None, None
        for idx, msg in enumerate(messages):
            # Every reply references the thread root + its immediate parent.
            reply_to = None
            if root is not None:
                reply_to = models.AppBskyFeedPost.ReplyRef(root=root, parent=parent)
            img = image_local_url if idx == 0 else None
            # The link card rides the first post, and only when no image claims its
            # embed slot there.
            emb = embed_url if (idx == 0 and not img) else None
            resp = self._send(client, msg, img, alt_text, reply_to, embed_url=emb)
            ref = models.create_strong_ref(resp)
            if root is None:
                root = ref
            parent = ref
            urls.append(self._post_url(resp.uri))
        return urls

    # ====================================================================================
    def config_filename(self):
        return 'settings_bsky_%s.ini' % self.hl

# ====================================================================================
if __name__ == '__main__':
    print("Commented to prevent accidental post")
    #bsky_en = PostBsky("en")
    #res = bsky_en.post(msg='Hello world! I posted this via the Python SDK.',
    #                image_local_url="richTextArea_en1.png")
    #print("Result:", res)
