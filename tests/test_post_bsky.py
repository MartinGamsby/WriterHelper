import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from post_bsky import build_rich_text  # noqa: E402


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
