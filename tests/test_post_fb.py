import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import post_fb  # noqa: E402
from post_fb import PostFB  # noqa: E402


# ========================================================================================
class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


@pytest.fixture
def fb(tmp_path, monkeypatch):
    """A PostFB with a known page id + token, built in a temp CWD so the default
    config write (and any settings file) lands in the tmp folder, not the repo."""
    monkeypatch.chdir(tmp_path)
    poster = PostFB("fr")
    poster.config["Access"]["PageId"] = "123"
    poster.config["Access"]["Token"] = "tok"
    return poster


# ========================================================================================
def test_get_token_and_page_id_both_survive_init(fb):
    # Regression: the old code assigned config['Access'] twice and dropped Token.
    assert fb.get_token() == "tok"
    assert fb.get_page_id() == "123"


def test_config_filename_is_fb_settings(fb):
    assert fb.config_filename() == "fb_settings_fr.ini"


def test_text_post_hits_feed_and_builds_url(fb, monkeypatch):
    calls = {}

    def fake_post(url, data=None, files=None):
        calls["url"], calls["data"], calls["files"] = url, data, files
        return FakeResponse({"id": "123_456"})

    monkeypatch.setattr(post_fb.requests, "post", fake_post)
    url = fb.post("Hello", image_local_url=None, alt_text="Hello")
    assert calls["url"].endswith("/123/feed")
    assert calls["files"] is None
    assert calls["data"] == {"message": "Hello", "access_token": "tok"}
    assert url == "https://www.facebook.com/123_456"


def test_image_post_hits_photos_uploads_source_and_uses_post_id(fb, tmp_path, monkeypatch):
    img = tmp_path / "card.png"
    img.write_bytes(b"png")
    calls = {}

    def fake_post(url, data=None, files=None):
        calls["url"], calls["data"], calls["files"] = url, data, files
        # /photos returns the photo id plus the feed-post id we want for the URL.
        return FakeResponse({"id": "photo999", "post_id": "123_789"})

    monkeypatch.setattr(post_fb.requests, "post", fake_post)
    url = fb.post("Caption", image_local_url=str(img), alt_text="alt here")
    assert calls["url"].endswith("/123/photos")
    assert "source" in calls["files"]
    assert calls["data"]["alt_text_custom"] == "alt here"
    assert url == "https://www.facebook.com/123_789"


def test_graph_error_is_raised(fb, monkeypatch):
    def fake_post(url, data=None, files=None):
        return FakeResponse({"error": {"code": 190, "message": "Invalid token"}}, 400)

    monkeypatch.setattr(post_fb.requests, "post", fake_post)
    with pytest.raises(RuntimeError, match="Invalid token"):
        fb.post("Hello", image_local_url=None, alt_text="")
