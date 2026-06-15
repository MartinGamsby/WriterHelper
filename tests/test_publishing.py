import os

import pytest

import publishing
from publishing import Platform


# ========================================================================================
class FakePoster:
    def __init__(self, hl):
        self.hl = hl

    def post(self, msg, image_local_url, alt_text):
        FakePoster.last = {"msg": msg, "image": image_local_url, "alt": alt_text}
        return "https://fake.example/post/1"

    def post_thread(self, messages, image_local_url, alt_text):
        FakePoster.last_thread = {"messages": list(messages),
                                  "image": image_local_url, "alt": alt_text}
        return ["https://fake.example/post/%d" % (n + 1) for n in range(len(messages))]


@pytest.fixture
def fake_x(monkeypatch):
    monkeypatch.setitem(publishing.PLATFORMS, "x",
                        Platform("x", "X / Twitter", "X/Twitter", 280, FakePoster))
    monkeypatch.setattr(publishing.webbrowser, "open", lambda url: None)
    return publishing.PLATFORMS["x"]


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
    assert FakePoster.last == {"msg": "Mon message", "image": None, "alt": "Mon message"}
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


def test_publish_image_requires_captured_png(fr, fake_x, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # no richTextArea_fr1.png here
    fr.set_facets(["dev"])
    result = publishing.publish(fr, "x", "image", "Titre")
    assert result["ok"] is False
    assert "richTextArea_fr1.png" in result["error"]


def test_publish_image_attaches_page_one(fr, fake_x, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "richTextArea_fr1.png").write_bytes(b"png")
    fr.set_title("Titre")
    fr.set_content("contenu")
    fr.set_facets(["dev"])
    result = publishing.publish(fr, "x", "image", "Titre")
    assert result["ok"] is True
    assert FakePoster.last["image"] == "richTextArea_fr1.png"
    assert "contenu" in FakePoster.last["alt"]


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
    monkeypatch.chdir(tmp_path)  # no richTextArea_fr1.png here
    fr.set_facets(["dev"])
    result = publishing.publish(fr, "x", "thread", "Un\n---\nDeux",
                                {"number": False, "image": "grabbed"})
    assert result["ok"] is False
    assert "richTextArea_fr1.png" in result["error"]


def test_publish_thread_attaches_grabbed_card_to_first(fr, fake_x, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "richTextArea_fr1.png").write_bytes(b"png")
    fr.set_title("Titre")
    fr.set_content("contenu")
    fr.set_facets(["dev"])
    result = publishing.publish(fr, "x", "thread", "Un\n---\nDeux",
                                {"number": False, "image": "grabbed"})
    assert result["ok"] is True
    assert FakePoster.last_thread["image"] == "richTextArea_fr1.png"
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
