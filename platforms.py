# The social platforms WriterHelper publishes to, and HOW each one is reached:
#   "api"     — a native adapter (post_*.py) posts directly (Bluesky; optionally X,
#               Facebook Page, Instagram Business);
#   "browser" — the post is queued as a job for Claude in Chrome, which posts it in the
#               operator's real, signed-in browser via the /chrome-post skill
#               ([[browser-hook]]). That reaches personal profiles (Facebook, LinkedIn)
#               and paid/closed APIs (X, TikTok, Threads…) with zero developer apps.
# No Qt. See [[publishing]] for the registry table.
import publish_config


# ========================================================================================
class Platform:
    def __init__(self, key, label, link_name, max_length, make_poster,
                 supports_thread=True, media="any", browser_url="",
                 default_transport=None):
        self.key = key
        self.label = label
        self.link_name = link_name      # the Link slot used as idempotence guard
        self.max_length = max_length
        # callable(hl) -> Post adapter, or None when the platform is browser-only.
        self.make_poster = make_poster
        # Whether a reply chain can be posted (adapter post_thread, or the browser
        # composer's "add post"). When False, a too-long post is offered as Image.
        self.supports_thread = supports_thread
        # What media the platform REQUIRES of a post: "any" (text or image), "image"
        # (mandatory — Pinterest, Instagram, TikTok photo posts) or "video" (nothing
        # WriterHelper can author yet; the popup gates it). See [[social-publishing]].
        self.media = media
        # Where Claude in Chrome starts composing; "" = no browser route.
        self.browser_url = browser_url
        self.default_transport = default_transport or ("api" if make_poster else "browser")

    # ====================================================================================
    def transports(self):
        return [t for t, ok in (("api", self.make_poster), ("browser", self.browser_url))
                if ok]

    @property
    def transport(self):
        """The route used right now: the operator's settings_publish.ini pin when it
        names an available route, else the default. Read live (no restart)."""
        pinned = publish_config.transport_override(self.key)
        return pinned if pinned in self.transports() else self.default_transport

    @property
    def via(self):
        """"browser" when the post goes through Claude in Chrome, "" when native.
        Drives the "(Chrome)" badge on the publish buttons."""
        return "browser" if self.transport == "browser" else ""


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


# Adapters import lazily (inside the factories) so a missing dependency doesn't break
# import and tests can monkeypatch the registry.
PLATFORMS = {
    # The one API that's free and trivial — always native.
    "bluesky": Platform("bluesky", "Bluesky", "Bluesky", 300, _make_bsky),
    # X's API is pay-per-use: default to the browser (threads work there too, via the
    # composer's "+"). Pin `x = api` to use the native tweepy adapter instead.
    "x": Platform("x", "X / Twitter", "X/Twitter", 280, _make_x,
                  browser_url="https://x.com/compose/post", default_transport="browser"),
    # The Graph API can only post to a Facebook *Page*; the browser posts on the
    # operator's personal profile. Pin `facebook = api` for the Page adapter.
    "facebook": Platform("facebook", "Facebook", "Facebook", 63206, _make_fb,
                         supports_thread=False, browser_url="https://www.facebook.com/",
                         default_transport="browser"),
    # Instagram's API needs a Business account AND a public image URL (the two-step
    # repo push, [[instagram-adapter]]). The browser uploads the local card directly.
    "instagram": Platform("instagram", "Instagram", "Instagram", 2200, _make_ig,
                          supports_thread=False, media="image",
                          browser_url="https://www.instagram.com/",
                          default_transport="browser"),
    # Browser-only platforms: no usable personal-account API.
    "linkedin": Platform("linkedin", "LinkedIn", "LinkedIn", 3000, None,
                         supports_thread=False,
                         browser_url="https://www.linkedin.com/feed/?shareActive=true"),
    "threads": Platform("threads", "Threads", "Threads", 500, None,
                        browser_url="https://www.threads.com/"),
    # Pins are image-first; the pin's destination link is the article URL.
    "pinterest": Platform("pinterest", "Pinterest", "Pinterest", 500, None,
                          supports_thread=False, media="image",
                          browser_url="https://www.pinterest.com/pin-creation-tool/"),
    # TikTok photo post (the card as a picture) — TikTok Studio's web uploader.
    "tiktok": Platform("tiktok", "TikTok", "TikTok", 2200, None,
                       supports_thread=False, media="image",
                       browser_url="https://www.tiktok.com/tiktokstudio/upload"),
    # Long-form: the whole article as a Medium story (title + body).
    "medium": Platform("medium", "Medium", "Medium", 100000, None,
                       supports_thread=False, browser_url="https://medium.com/new-story"),
}


def is_hidden(platform_key) -> bool:
    """Operator-hidden platforms (settings_publish.ini [Hidden]) lose their publish
    button; an already-filled link slot still shows as a plain field."""
    return platform_key in publish_config.hidden_platforms()
