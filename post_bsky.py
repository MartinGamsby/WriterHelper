import os
import re
from atproto import Client, client_utils, models
from post import Post

# A bare http(s) URL. Bluesky leaves URLs as plain (un-clickable) text unless the
# post carries link *facets*; we detect them here and build those facets.
_URL_RE = re.compile(r'https?://[^\s<>"\']+')
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
    def _send(self, client, msg, image_local_url, alt_text, reply_to):
        """One post (optionally with an image, optionally a reply). Returns the SDK
        response (carries .uri/.cid for building the next reply ref)."""
        # A TextBuilder when the text has URLs (→ clickable link facets), else the
        # plain string. send_post/send_image accept either.
        text = build_rich_text(msg)
        if image_local_url and os.path.isfile(image_local_url):
            with open(image_local_url, 'rb') as f:
                return client.send_image(text=text, image=f.read(), image_alt=alt_text,
                                         langs=[self.hl], reply_to=reply_to)
        return client.send_post(text, langs=[self.hl], reply_to=reply_to)

    # ====================================================================================
    def post(self, msg, image_local_url, alt_text):
        client = Client()
        client.login(self.get_handle(), self.get_app_password())
        # More than text here: https://docs.bsky.app/docs/tutorials/creating-a-post
        post = self._send(client, msg, image_local_url, alt_text, reply_to=None)
        return self._post_url(post.uri)

    # ====================================================================================
    def post_thread(self, messages, image_local_url, alt_text):
        client = Client()
        client.login(self.get_handle(), self.get_app_password())
        urls, root, parent = [], None, None
        for idx, msg in enumerate(messages):
            # Every reply references the thread root + its immediate parent.
            reply_to = None
            if root is not None:
                reply_to = models.AppBskyFeedPost.ReplyRef(root=root, parent=parent)
            img = image_local_url if idx == 0 else None
            resp = self._send(client, msg, img, alt_text, reply_to)
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
