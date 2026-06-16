import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import post_bsky  # noqa: E402
from post_bsky import build_rich_text, fetch_external_card, youtube_id  # noqa: E402


# ========================================================================================
def _facets(tb):
    """(text, [(url, substring)]) extracted from a TextBuilder for assertions."""
    text = tb.build_text()
    links = []
    for facet in tb.build_facets():
        for feature in facet.features:
            uri = getattr(feature, "uri", None)
            if uri:
                seg = text.encode("utf-8")[facet.index.byte_start:facet.index.byte_end]
                links.append((uri, seg.decode("utf-8")))
    return text, links


# ========================================================================================
def test_no_url_returns_plain_string_unchanged():
    # No URL → behaviour identical to before (a bare str, not a TextBuilder).
    assert build_rich_text("Just a normal post, nothing to link.") == \
        "Just a normal post, nothing to link."


def test_single_url_becomes_a_link_facet():
    tb = build_rich_text("Read it here: https://martingamsby.com/en/foo")
    text, links = _facets(tb)
    assert text == "Read it here: https://martingamsby.com/en/foo"
    assert links == [("https://martingamsby.com/en/foo",
                      "https://martingamsby.com/en/foo")]


def test_two_urls_each_get_their_own_facet():
    tb = build_rich_text("A https://a.example and B https://b.example end")
    text, links = _facets(tb)
    assert text == "A https://a.example and B https://b.example end"
    assert [u for u, _ in links] == ["https://a.example", "https://b.example"]
    # The facet byte ranges must cover exactly the URLs, not the surrounding words.
    assert all(uri == seg for uri, seg in links)


def test_trailing_sentence_punctuation_is_not_part_of_the_link():
    tb = build_rich_text("See https://martingamsby.com/x.")
    _, links = _facets(tb)
    assert links == [("https://martingamsby.com/x", "https://martingamsby.com/x")]


def test_wrapping_parens_are_trimmed_but_internal_ones_survive():
    tb = build_rich_text("(https://en.wikipedia.org/wiki/Foo_(bar))")
    _, links = _facets(tb)
    # The wrapping ")" is dropped; the balanced "(bar)" inside the URL stays.
    assert links == [("https://en.wikipedia.org/wiki/Foo_(bar)",
                      "https://en.wikipedia.org/wiki/Foo_(bar)")]


def test_unicode_before_url_keeps_byte_offsets_correct():
    # Facet indices are BYTE offsets; multi-byte text before the URL must be accounted
    # for or the link would land on the wrong characters.
    tb = build_rich_text("Voilà → https://martingamsby.com/fr")
    text, links = _facets(tb)
    assert links == [("https://martingamsby.com/fr", "https://martingamsby.com/fr")]


# ========================================================================================
# YouTube id extraction
@pytest.mark.parametrize("url, vid", [
    ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("https://martingamsby.com/en/foo", None),
    ("", None),
])
def test_youtube_id(url, vid):
    assert youtube_id(url) == vid


# ========================================================================================
# External link-card embed
class FakeResp:
    def __init__(self, text="", content=b"", status=200):
        self.text, self.content, self.status_code = text, content, status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("HTTP %d" % self.status_code)


class FakeBlobResp:
    def __init__(self):
        self.blob = "BLOB_REF"


class FakeClient:
    def __init__(self):
        self.uploaded = None

    def upload_blob(self, data):
        self.uploaded = data
        return FakeBlobResp()


_HTML = """<html><head>
    <meta property="og:title" content="My Article">
    <meta property="og:description" content="A great read.">
    <meta property="og:image" content="https://img.example/cover.jpg">
</head></html>"""


def test_fetch_external_card_builds_from_opengraph(monkeypatch):
    def fake_get(url, timeout=None, headers=None):
        return FakeResp(text=_HTML) if "img.example" not in url else FakeResp(content=b"imgbytes")
    monkeypatch.setattr(post_bsky.requests, "get", fake_get)
    client = FakeClient()
    embed = fetch_external_card(client, "https://martingamsby.com/en/foo")
    assert embed.external.uri == "https://martingamsby.com/en/foo"
    assert embed.external.title == "My Article"
    assert embed.external.description == "A great read."
    assert embed.external.thumb == "BLOB_REF"
    assert client.uploaded == b"imgbytes"


def test_fetch_external_card_youtube_uses_img_youtube_thumbnail(monkeypatch):
    seen = {}

    def fake_get(url, timeout=None, headers=None):
        seen.setdefault("urls", []).append(url)
        return FakeResp(text="<html><head><title>Vid</title></head></html>") \
            if "img.youtube" not in url else FakeResp(content=b"thumb")
    monkeypatch.setattr(post_bsky.requests, "get", fake_get)
    embed = fetch_external_card(FakeClient(), "https://youtu.be/dQw4w9WgXcQ")
    # The thumbnail is fetched from the reliable img.youtube.com URL, not scraped.
    assert any("img.youtube.com/vi/dQw4w9WgXcQ/" in u for u in seen["urls"])
    assert embed.external.thumb == "BLOB_REF"


def test_fetch_external_card_returns_none_on_fetch_failure(monkeypatch):
    def fake_get(url, timeout=None, headers=None):
        raise RuntimeError("network down")
    monkeypatch.setattr(post_bsky.requests, "get", fake_get)
    # A missing card must never block the post — caller posts plain instead.
    assert fetch_external_card(FakeClient(), "https://x.example") is None


def test_fetch_external_card_survives_missing_thumbnail(monkeypatch):
    def fake_get(url, timeout=None, headers=None):
        if "cover" in url:
            return FakeResp(status=404)          # image fetch fails
        return FakeResp(text=_HTML)
    monkeypatch.setattr(post_bsky.requests, "get", fake_get)
    embed = fetch_external_card(FakeClient(), "https://martingamsby.com/en/foo")
    assert embed.external.title == "My Article"
    assert embed.external.thumb is None          # no thumb, but the card still posts
