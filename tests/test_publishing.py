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


def test_prepare_flags_missing_facet(fr):
    fr.set_title("Sans facette")
    info = publishing.prepare_post(fr, "x")     # no facet set
    assert info["facets_ok"] is False


def test_prepare_long_content_suggests_image(fr):
    fr.set_title("Long")
    fr.set_content("mot " * 200)
    info = publishing.prepare_post(fr, "x")
    assert info["fits"] is False
    assert info["suggested_mode"] == "image"
    assert info["text_length"] > 280


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
