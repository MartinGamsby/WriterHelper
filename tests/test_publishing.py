import base64
import os

import pytest

import publishing
import rendering
from publishing import Platform


# ========================================================================================
class FakePoster:
    def __init__(self, hl):
        self.hl = hl

    def post(self, msg, image_local_url, alt_text, embed_url=None):
        FakePoster.last = {"msg": msg, "image": image_local_url, "alt": alt_text,
                           "embed_url": embed_url}
        return "https://fake.example/post/1"

    def post_thread(self, messages, image_local_url, alt_text, embed_url=None):
        FakePoster.last_thread = {"messages": list(messages),
                                  "image": image_local_url, "alt": alt_text,
                                  "embed_url": embed_url}
        return ["https://fake.example/post/%d" % (n + 1) for n in range(len(messages))]


@pytest.fixture
def fake_x(monkeypatch):
    monkeypatch.setitem(publishing.PLATFORMS, "x",
                        Platform("x", "X / Twitter", "X/Twitter", 280, FakePoster))
    monkeypatch.setattr(publishing.webbrowser, "open", lambda url: None)
    return publishing.PLATFORMS["x"]


@pytest.fixture
def fake_fb(monkeypatch):
    monkeypatch.setitem(publishing.PLATFORMS, "facebook",
                        Platform("facebook", "Facebook", "Facebook", 63206, FakePoster))
    monkeypatch.setattr(publishing.webbrowser, "open", lambda url: None)
    return publishing.PLATFORMS["facebook"]


@pytest.fixture
def fake_bsky(monkeypatch):
    monkeypatch.setitem(publishing.PLATFORMS, "bluesky",
                        Platform("bluesky", "Bluesky", "Bluesky", 300, FakePoster))
    monkeypatch.setattr(publishing.webbrowser, "open", lambda url: None)
    return publishing.PLATFORMS["bluesky"]


# ========================================================================================
def test_prepare_short_content_suggests_text(fr, monkeypatch):
    monkeypatch.chdir(os.path.dirname(fr.get_posts_folder()))
    fr.set_title("Court")
    fr.set_content("Très court contenu.")
    fr.set_facets(["dev"])
    info = publishing.prepare_post(fr, "x")
    assert info["fits"] is True
    assert info["suggested_mode"] == "text"
    assert "Très court contenu." in info["text"]
    assert "Court" in info["text"]
    assert info["existing_url"] == ""
    assert info["image_exists"] is False
    assert info["max_length"] == 280
    assert info["facets_ok"] is True
    assert info["article_image_exists"] is False    # no excerpt image set


def test_plain_text_separates_paragraphs_with_blank_line(fr):
    fr.set_title("Titre")
    fr.set_content("Premier paragraphe.\n\nDeuxième paragraphe.")
    text = rendering.plain_text(fr)
    assert "Premier paragraphe." in text and "Deuxième paragraphe." in text
    # A blank line between paragraphs, and they're never mashed onto one line.
    assert "Premier paragraphe.\n\nDeuxième paragraphe." in text
    assert "paragraphe.Deuxième" not in text and "paragraphe. Deuxième" not in text


def test_prepare_flags_missing_facet(fr):
    fr.set_title("Sans facette")
    info = publishing.prepare_post(fr, "x")     # no facet set
    assert info["facets_ok"] is False


def test_prepare_long_content_suggests_thread(fr):
    fr.set_title("Long")
    fr.set_content("mot " * 200)
    info = publishing.prepare_post(fr, "x")
    assert info["fits"] is False
    assert info["suggested_mode"] == "thread"
    assert info["text_length"] > 280
    # The editable thread blob is split into multiple `---`-separated segments.
    assert info["thread_count"] > 1
    assert info["separator"] in info["thread_text"]


def test_prepare_short_content_thread_is_single_segment(fr, monkeypatch):
    monkeypatch.chdir(os.path.dirname(fr.get_posts_folder()))
    fr.set_title("Court")
    fr.set_content("Très court.")
    fr.set_facets(["dev"])
    info = publishing.prepare_post(fr, "x")
    assert info["thread_count"] == 1
    assert info["separator"] not in info["thread_text"]


# ========================================================================================
def test_publish_text_posts_and_records_link(fr, fake_x):
    fr.set_title("Court")
    fr.set_facets(["dev"])
    result = publishing.publish(fr, "x", "text", "Mon message")
    assert result["ok"] is True
    assert result["url"] == "https://fake.example/post/1"
    assert FakePoster.last == {"msg": "Mon message", "image": None, "alt": "Mon message",
                               "embed_url": None}
    assert fr.get_link("X/Twitter") == result["url"]


def test_publish_blocks_without_facet(fr, fake_x):
    fr.set_title("Sans facette")              # no facet → mandatory rule blocks the post
    result = publishing.publish(fr, "x", "text", "Mon message")
    assert result["ok"] is False
    assert "facet" in result["error"].lower()


def test_publish_guard_blocks_double_post(fr, fake_x):
    fr.set_facets(["dev"])
    fr.set_link("X/Twitter", "https://existing.example")
    result = publishing.publish(fr, "x", "text", "Encore")
    assert result["ok"] is False
    assert result["url"] == "https://existing.example"


def test_publish_text_rejects_over_limit(fr, fake_x):
    fr.set_facets(["dev"])
    result = publishing.publish(fr, "x", "text", "x" * 281)
    assert result["ok"] is False
    assert "281" in result["error"]


def test_image_filename_is_slug_named_jpg(fr):
    fr.set_title("Mon Titre")
    assert publishing.image_filename(fr) == "richTextArea_mon-titre_fr1.jpg"


def test_save_capture_writes_the_name_publishing_expects(pair, tmp_path, monkeypatch):
    # Close the producer↔consumer loop: webapi.save_capture must write exactly the
    # file publishing.image_filename() will later look for.
    from webapi import Api
    monkeypatch.chdir(tmp_path)
    fr = pair.fr()
    fr.set_title("Mon Titre")
    data_url = "data:image/jpeg;base64," + base64.b64encode(b"jpgbytes").decode()
    name = Api(pair).save_capture("fr", 1, data_url)
    assert name == publishing.image_filename(fr) == "richTextArea_mon-titre_fr1.jpg"
    assert (tmp_path / name).read_bytes() == b"jpgbytes"


def test_publish_image_requires_captured_png(fr, fake_x, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # no capture here
    fr.set_title("Titre")
    fr.set_facets(["dev"])
    result = publishing.publish(fr, "x", "image", "Titre")
    assert result["ok"] is False
    assert publishing.image_filename(fr) in result["error"]


def test_publish_image_attaches_page_one(fr, fake_x, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fr.set_title("Titre")
    fr.set_content("contenu")
    fr.set_facets(["dev"])
    (tmp_path / publishing.image_filename(fr)).write_bytes(b"jpg")
    result = publishing.publish(fr, "x", "image", "Titre")
    assert result["ok"] is True
    assert FakePoster.last["image"] == publishing.image_filename(fr)
    assert "contenu" in FakePoster.last["alt"]


def test_publish_image_resolves_by_current_article_slug(fr, fake_x, tmp_path, monkeypatch):
    # A capture exists, but for a DIFFERENT article (different slug) — it must NOT
    # be picked up for the current one. This is the "right article" guarantee.
    monkeypatch.chdir(tmp_path)
    fr.set_title("Premier")
    fr.set_facets(["dev"])
    (tmp_path / "richTextArea_autre-article_fr1.jpg").write_bytes(b"jpg")
    result = publishing.publish(fr, "x", "image", "Premier")
    assert result["ok"] is False                       # nothing grabbed for "premier"
    # Grab for the current article → now it publishes.
    (tmp_path / publishing.image_filename(fr)).write_bytes(b"jpg")
    result = publishing.publish(fr, "x", "image", "Premier")
    assert result["ok"] is True
    assert FakePoster.last["image"] == "richTextArea_premier_fr1.jpg"


# ========================================================================================
def test_facebook_long_text_still_fits(fr):
    fr.set_title("Long")
    fr.set_content("mot " * 200)        # over X's 280 but well under Facebook's limit
    info = publishing.prepare_post(fr, "facebook")
    assert info["label"] == "Facebook"
    assert info["max_length"] == 63206
    assert info["fits"] is True
    assert info["suggested_mode"] == "text"


def test_publish_facebook_text_records_facebook_link(fr, fake_fb):
    fr.set_title("Bonjour")
    fr.set_facets(["dev"])
    result = publishing.publish(fr, "facebook", "text", "Mon message FB")
    assert result["ok"] is True
    assert FakePoster.last == {"msg": "Mon message FB", "image": None,
                               "alt": "Mon message FB", "embed_url": None}
    assert fr.get_link("Facebook") == result["url"]


def test_publish_facebook_image_attaches_card(fr, fake_fb, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fr.set_title("Titre")
    fr.set_content("contenu")
    fr.set_facets(["dev"])
    (tmp_path / publishing.image_filename(fr)).write_bytes(b"jpg")
    result = publishing.publish(fr, "facebook", "image", "Titre")
    assert result["ok"] is True
    assert FakePoster.last["image"] == publishing.image_filename(fr)


# ========================================================================================
# Bluesky link-preview card (embed)
def test_embed_candidate_prefers_youtube_slot_over_message_url(fr):
    fr.set_link("YouTube", "https://youtu.be/abc")
    # Even with a different URL in the message, the deliberate YouTube slot wins.
    assert publishing.embed_candidate(fr, "see https://example.com/x") == "https://youtu.be/abc"


def test_embed_candidate_falls_back_to_first_message_url(fr):
    got = publishing.embed_candidate(fr, "read https://martingamsby.com/en/foo, nice.")
    assert got == "https://martingamsby.com/en/foo"   # trailing comma trimmed


def test_embed_candidate_empty_when_no_link(fr):
    assert publishing.embed_candidate(fr, "no links here") == ""


def test_prepare_exposes_embed_url_for_bluesky_only(fr, monkeypatch):
    monkeypatch.chdir(os.path.dirname(fr.get_posts_folder()))
    fr.set_title("Court")
    fr.set_content("Court.")
    fr.set_facets(["dev"])
    fr.set_link("YouTube", "https://youtu.be/abc")
    assert publishing.prepare_post(fr, "bluesky")["embed_url"] == "https://youtu.be/abc"
    assert publishing.prepare_post(fr, "x")["embed_url"] == ""   # X auto-unfurls


def test_publish_text_passes_embed_url_when_opted_in(fr, fake_bsky):
    fr.set_facets(["dev"])
    fr.set_link("YouTube", "https://youtu.be/abc")
    result = publishing.publish(fr, "bluesky", "text", "Watch this", {"embed": True})
    assert result["ok"] is True
    assert FakePoster.last["embed_url"] == "https://youtu.be/abc"


def test_publish_text_no_embed_when_not_opted_in(fr, fake_bsky):
    fr.set_facets(["dev"])
    fr.set_link("YouTube", "https://youtu.be/abc")
    publishing.publish(fr, "bluesky", "text", "Watch this", {"embed": False})
    assert FakePoster.last["embed_url"] is None


def test_publish_thread_passes_embed_url_when_opted_in(fr, fake_bsky):
    fr.set_facets(["dev"])
    fr.set_link("YouTube", "https://youtu.be/abc")
    publishing.publish(fr, "bluesky", "thread", "Un\n---\nDeux",
                       {"number": False, "image": "none", "embed": True})
    assert FakePoster.last_thread["embed_url"] == "https://youtu.be/abc"


def test_publish_non_bluesky_ignores_embed_option(fr, fake_x):
    # X auto-unfurls, so even an opted-in embed must not pass a URL to its adapter.
    fr.set_facets(["dev"])
    fr.set_link("YouTube", "https://youtu.be/abc")
    publishing.publish(fr, "x", "text", "Watch this", {"embed": True})
    assert FakePoster.last["embed_url"] is None


# ========================================================================================
def test_publish_thread_posts_chain_and_records_first(fr, fake_x):
    fr.set_facets(["dev"])
    message = "First part.\n---\nSecond part.\n---\nThird part."
    result = publishing.publish(fr, "x", "thread", message,
                                {"number": False, "image": "none"})
    assert result["ok"] is True
    assert result["url"] == "https://fake.example/post/1"
    assert result["urls"] == ["https://fake.example/post/%d" % n for n in (1, 2, 3)]
    assert FakePoster.last_thread["messages"] == ["First part.", "Second part.", "Third part."]
    assert FakePoster.last_thread["image"] is None
    # Only the first post's URL is the idempotence guard.
    assert fr.get_link("X/Twitter") == "https://fake.example/post/1"


def test_publish_thread_numbers_segments_when_requested(fr, fake_x):
    fr.set_facets(["dev"])
    result = publishing.publish(fr, "x", "thread", "Un\n---\nDeux",
                                {"number": True, "image": "none"})
    assert result["ok"] is True
    assert FakePoster.last_thread["messages"] == ["Un (1/2)", "Deux (2/2)"]


def test_publish_thread_rejects_over_limit_segment(fr, fake_x):
    fr.set_facets(["dev"])
    message = "ok\n---\n" + "x" * 281
    result = publishing.publish(fr, "x", "thread", message, {"number": False})
    assert result["ok"] is False
    assert "2" in result["error"]


def test_publish_thread_empty_message_blocked(fr, fake_x):
    fr.set_facets(["dev"])
    result = publishing.publish(fr, "x", "thread", "   \n---\n   ", {"number": False})
    assert result["ok"] is False


def test_publish_thread_grabbed_image_requires_captured_png(fr, fake_x, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # no capture here
    fr.set_title("Titre")
    fr.set_facets(["dev"])
    result = publishing.publish(fr, "x", "thread", "Un\n---\nDeux",
                                {"number": False, "image": "grabbed"})
    assert result["ok"] is False
    assert publishing.image_filename(fr) in result["error"]


def test_publish_thread_attaches_grabbed_card_to_first(fr, fake_x, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fr.set_title("Titre")
    fr.set_content("contenu")
    fr.set_facets(["dev"])
    (tmp_path / publishing.image_filename(fr)).write_bytes(b"jpg")
    result = publishing.publish(fr, "x", "thread", "Un\n---\nDeux",
                                {"number": False, "image": "grabbed"})
    assert result["ok"] is True
    assert FakePoster.last_thread["image"] == publishing.image_filename(fr)
    # The grabbed card carries the whole article, so its alt text is the full text.
    assert "contenu" in FakePoster.last_thread["alt"]


def test_publish_thread_attaches_article_image_to_first(fr, fake_x, tmp_path):
    header = tmp_path / "header.webp"
    header.write_bytes(b"webp")
    fr.set_title("Titre")
    fr.set_excerpt_img(str(header))   # absolute local path → resolves as the article image
    fr.set_facets(["dev"])
    result = publishing.publish(fr, "x", "thread", "Un\n---\nDeux",
                                {"number": False, "image": "article"})
    assert result["ok"] is True
    assert FakePoster.last_thread["image"] == str(header)
    # The header image is decorative, so its alt text is the title (not the body).
    assert FakePoster.last_thread["alt"] == "Titre"


def test_publish_thread_article_image_missing_is_reported(fr, fake_x):
    fr.set_facets(["dev"])                 # no excerpt image set
    result = publishing.publish(fr, "x", "thread", "Un\n---\nDeux",
                                {"number": False, "image": "article"})
    assert result["ok"] is False
    assert "image" in result["error"].lower()
