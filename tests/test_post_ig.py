import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import post_ig  # noqa: E402
from post_ig import PostIG  # noqa: E402


# ========================================================================================
class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


@pytest.fixture
def ig(tmp_path, monkeypatch):
    """A PostIG with a known IG user id + token, built in a temp CWD so the default
    config write lands in tmp, not the repo."""
    monkeypatch.chdir(tmp_path)
    poster = PostIG("fr")
    poster.config["Access"]["IgUserId"] = "17890"
    poster.config["Access"]["Token"] = "tok"
    return poster


# ========================================================================================
def test_reuses_facebook_settings_file(ig):
    # IG rides the FB Page token, so it shares settings_fb_<hl>.ini (+ an IgUserId line).
    assert ig.config_filename() == "settings_fb_fr.ini"


def test_handle_is_the_ig_user_id(ig):
    # The base __init__ logs get_handle(); IG has no handle, so it surfaces the IG id.
    assert ig.get_handle() == "17890"


def test_post_creates_container_publishes_then_returns_permalink(ig, monkeypatch):
    calls = []

    def fake_post(url, data=None, files=None):
        calls.append((url, data))
        if url.endswith("/media"):
            return FakeResponse({"id": "container-1"})
        if url.endswith("/media_publish"):
            return FakeResponse({"id": "media-9"})
        raise AssertionError("unexpected POST %s" % url)

    def fake_get(url, params=None):
        calls.append((url, params))
        assert url.endswith("/media-9")
        assert params["fields"] == "permalink"
        return FakeResponse({"permalink": "https://www.instagram.com/p/ABC/"})

    monkeypatch.setattr(post_ig.requests, "post", fake_post)
    monkeypatch.setattr(post_ig.requests, "get", fake_get)

    url = ig.post(msg="Bonjour", image_url="https://raw.example/x.jpg")
    assert url == "https://www.instagram.com/p/ABC/"

    container_url, container_data = calls[0]
    assert container_url.endswith("/17890/media")
    assert container_data["image_url"] == "https://raw.example/x.jpg"
    assert container_data["caption"] == "Bonjour"

    publish_url, publish_data = calls[1]
    assert publish_url.endswith("/17890/media_publish")
    assert publish_data["creation_id"] == "container-1"


def test_post_without_image_url_raises(ig):
    # IG never uploads a local file — without a public image_url there's nothing to post.
    with pytest.raises(RuntimeError, match="public image_url"):
        ig.post(msg="x", image_url=None)


def test_graph_error_on_container_is_raised(ig, monkeypatch):
    def fake_post(url, data=None, files=None):
        return FakeResponse({"error": {"code": 9007, "message": "Media not ready"}}, 400)

    monkeypatch.setattr(post_ig.requests, "post", fake_post)
    with pytest.raises(RuntimeError, match="Media not ready"):
        ig.post(msg="x", image_url="https://raw.example/x.jpg")


def test_published_but_no_permalink_raises_with_media_id(ig, monkeypatch):
    # The post DID publish but the URL didn't read back — the error names the media id so
    # the operator can set the link by hand instead of blindly re-posting.
    def fake_post(url, data=None, files=None):
        return (FakeResponse({"id": "container-1"}) if url.endswith("/media")
                else FakeResponse({"id": "media-42"}))

    monkeypatch.setattr(post_ig.requests, "post", fake_post)
    monkeypatch.setattr(post_ig.requests, "get",
                        lambda url, params=None: FakeResponse({}))   # no permalink
    with pytest.raises(RuntimeError, match="media-42"):
        ig.post(msg="x", image_url="https://raw.example/x.jpg")
