import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import post_bridge  # noqa: E402
from post_bridge import PostBridge, PostBridgeError  # noqa: E402


# ========================================================================================
class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.ok = 200 <= status_code < 300
        self.text = str(payload)

    def json(self):
        return self._payload


@pytest.fixture
def bridge(tmp_path, monkeypatch):
    """A PostBridge with a known API key, built in a temp CWD so the default config
    write lands in tmp, not the repo. No polling delay during tests."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(post_bridge, "_RESULT_DELAY", 0)
    poster = PostBridge("en", "linkedin")
    poster.config["Access"]["ApiKey"] = "pb_live_test"
    return poster


# ========================================================================================
def test_shared_config_filename_no_hl(bridge):
    # One key serves every platform AND both languages, so the file is hl-independent.
    assert bridge.config_filename() == "settings_postbridge.ini"


def test_missing_key_is_a_clear_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    poster = PostBridge("en", "linkedin")            # ApiKey stays "<TODO>"
    with pytest.raises(PostBridgeError, match="API key is missing"):
        poster.list_accounts()


def test_twitter_alias_maps_to_x():
    assert PostBridge.__new__(PostBridge) is not None  # cheap sanity
    poster = PostBridge.__new__(PostBridge)
    poster.platform = post_bridge._PLATFORM_ALIASES.get("twitter", "twitter")
    assert poster.platform == "x"


# ---- account resolution -----------------------------------------------------------
def test_single_matching_account_auto_resolves(bridge, monkeypatch):
    monkeypatch.setattr(bridge, "list_accounts",
                        lambda: [{"id": 7, "platform": "linkedin", "username": "me"},
                                 {"id": 8, "platform": "threads", "username": "me"}])
    assert bridge._resolve_account_ids() == [7]


def test_no_matching_account_refuses(bridge, monkeypatch):
    monkeypatch.setattr(bridge, "list_accounts",
                        lambda: [{"id": 8, "platform": "threads", "username": "x"}])
    with pytest.raises(PostBridgeError, match="No linkedin account"):
        bridge._resolve_account_ids()


def test_several_accounts_without_pin_refuses_with_listing(bridge, monkeypatch):
    # A bilingual post must never land on the wrong-language account by guesswork.
    monkeypatch.setattr(bridge, "list_accounts",
                        lambda: [{"id": 7, "platform": "linkedin", "username": "en"},
                                 {"id": 9, "platform": "linkedin", "username": "fr"}])
    with pytest.raises(PostBridgeError, match=r"Pin the right one"):
        bridge._resolve_account_ids()


def test_language_pin_wins_over_autoresolve(bridge, monkeypatch):
    bridge.config["Accounts"]["linkedin_en"] = "7"
    bridge.config["Accounts"]["linkedin"] = "99"
    # list_accounts must not even be consulted when a pin exists.
    monkeypatch.setattr(bridge, "list_accounts",
                        lambda: (_ for _ in ()).throw(AssertionError("queried")))
    assert bridge._resolve_account_ids() == [7]


def test_bare_platform_pin_used_when_no_language_key(bridge, monkeypatch):
    bridge.config["Accounts"]["linkedin"] = "7, 9"
    assert bridge._resolve_account_ids() == [7, 9]


# ---- posting ----------------------------------------------------------------------
def test_text_post_resolves_public_url(bridge, monkeypatch):
    monkeypatch.setattr(bridge, "_resolve_account_ids", lambda: [7])
    posts = []

    def fake_post(url, headers=None, json=None, timeout=None):
        posts.append((url, json))
        assert url.endswith("/v1/posts")
        assert json == {"caption": "Hello", "social_accounts": [7]}
        return FakeResponse({"id": "post-1", "status": "processing"})

    def fake_get(url, headers=None, params=None, timeout=None):
        assert url.endswith("/v1/post-results")
        assert params == {"post_id": "post-1"}
        return FakeResponse({"data": [
            {"social_account_id": 7, "success": True,
             "platform_data": {"url": "https://linkedin.com/feed/update/1"}}]})

    monkeypatch.setattr(post_bridge.requests, "post", fake_post)
    monkeypatch.setattr(post_bridge.requests, "get", fake_get)

    url = bridge.post(msg="Hello", image_local_url=None, alt_text="Hello")
    assert url == "https://linkedin.com/feed/update/1"
    assert len(posts) == 1


def test_image_post_uploads_then_attaches_media(bridge, tmp_path, monkeypatch):
    monkeypatch.setattr(bridge, "_resolve_account_ids", lambda: [7])
    img = tmp_path / "card.jpg"
    img.write_bytes(b"\xff\xd8\xff\xe0jpegbytes")
    seen = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        if url.endswith("/create-upload-url"):
            seen["upload_req"] = json
            return FakeResponse({"media_id": "m-1",
                                 "upload_url": "https://signed.example/put"})
        if url.endswith("/v1/posts"):
            seen["post_body"] = json
            return FakeResponse({"id": "post-9"})
        raise AssertionError("unexpected POST %s" % url)

    def fake_put(url, data=None, headers=None, timeout=None):
        seen["put_url"] = url
        seen["put_ct"] = headers["Content-Type"]
        return FakeResponse({}, 200)

    def fake_get(url, headers=None, params=None, timeout=None):
        return FakeResponse({"data": [
            {"social_account_id": 7, "success": True,
             "platform_data": {"url": "https://pin.example/p/1"}}]})

    monkeypatch.setattr(post_bridge.requests, "post", fake_post)
    monkeypatch.setattr(post_bridge.requests, "put", fake_put)
    monkeypatch.setattr(post_bridge.requests, "get", fake_get)

    url = bridge.post(msg="Cap", image_local_url=str(img), alt_text="Cap")
    assert url == "https://pin.example/p/1"
    assert seen["upload_req"]["mime_type"] == "image/jpeg"
    assert seen["upload_req"]["size_bytes"] == img.stat().st_size
    assert seen["put_url"] == "https://signed.example/put"
    assert seen["put_ct"] == "image/jpeg"
    assert seen["post_body"]["media"] == ["m-1"]


def test_failed_result_row_raises_platform_error(bridge, monkeypatch):
    monkeypatch.setattr(bridge, "_resolve_account_ids", lambda: [7])
    monkeypatch.setattr(post_bridge.requests, "post",
                        lambda *a, **k: FakeResponse({"id": "post-1"}))
    monkeypatch.setattr(post_bridge.requests, "get",
                        lambda *a, **k: FakeResponse({"data": [
                            {"social_account_id": 7, "success": False,
                             "error": "token expired"}]}))
    with pytest.raises(PostBridgeError, match="token expired"):
        bridge.post(msg="x", image_local_url=None, alt_text="x")


def test_url_never_resolves_raises_manual_link_hint(bridge, monkeypatch):
    monkeypatch.setattr(bridge, "_resolve_account_ids", lambda: [7])
    monkeypatch.setattr(post_bridge, "_RESULT_POLLS", 2)
    monkeypatch.setattr(post_bridge.requests, "post",
                        lambda *a, **k: FakeResponse({"id": "post-1"}))
    # Still processing: a success row with no URL yet, every poll.
    monkeypatch.setattr(post_bridge.requests, "get",
                        lambda *a, **k: FakeResponse({"data": [
                            {"social_account_id": 7, "success": True,
                             "platform_data": {}}]}))
    with pytest.raises(PostBridgeError, match="copy the post URL"):
        bridge.post(msg="x", image_local_url=None, alt_text="x")


def test_unsupported_image_type_rejected(bridge, tmp_path, monkeypatch):
    monkeypatch.setattr(bridge, "_resolve_account_ids", lambda: [7])
    bad = tmp_path / "clip.gif"
    bad.write_bytes(b"GIF89a")
    with pytest.raises(PostBridgeError, match="JPEG or PNG"):
        bridge.post(msg="x", image_local_url=str(bad), alt_text="x")


def test_thread_not_supported(bridge):
    # post-bridge has no native reply chain — Thread mode must surface a clean error.
    with pytest.raises(NotImplementedError):
        bridge.post_thread(["a", "b"], None, "alt")
