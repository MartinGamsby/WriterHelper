# Publishing through the browser hook (transport "browser"), the transport registry,
# and the meta panel's link slots. See [[browser-hook]].
import os

import pytest

import browser_jobs
import publishing
import webapi
from platforms import Platform


# ========================================================================================
@pytest.fixture
def ready(fr, tmp_path, monkeypatch):
    """A publishable FR article with a grabbed card in the CWD."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(publishing.webbrowser, "open", lambda url: None)
    fr.set_title("Mon Titre")
    fr.set_content("Un court texte.")
    fr.set_facets(["dev"])
    (tmp_path / publishing.image_filename(fr)).write_bytes(b"jpg")
    return fr


# ---- registry / transport ---------------------------------------------------------
def test_default_transports():
    t = {k: p.transport for k, p in publishing.PLATFORMS.items()}
    assert t["bluesky"] == "api"
    for k in ("x", "facebook", "instagram", "linkedin", "threads", "pinterest",
              "tiktok", "medium"):
        assert t[k] == "browser", k


def test_transport_pin_switches_to_api_only_where_an_adapter_exists(publish_ini):
    publish_ini("[Transport]\nx = api\nfacebook = API\nlinkedin = api\nbluesky = browser\n")
    P = publishing.PLATFORMS
    assert P["x"].transport == "api" and P["x"].via == ""
    assert P["facebook"].transport == "api"           # case-insensitive
    assert P["linkedin"].transport == "browser"       # no adapter → pin ignored
    assert P["bluesky"].transport == "api"            # no browser route → pin ignored


def test_no_post_bridge_left():
    assert all(p.via in ("", "browser") for p in publishing.PLATFORMS.values())
    assert not os.path.exists(os.path.join(os.path.dirname(publishing.__file__),
                                           "post_bridge.py"))


def test_prepare_exposes_transport_and_pending_job(ready):
    info = publishing.prepare_post(ready, "linkedin")
    assert (info["transport"], info["via"]) == ("browser", "browser")
    assert info["compose_url"].startswith("https://www.linkedin.com/")
    assert info["pending_job"] is None
    publishing.publish(ready, "linkedin", "text", "Bonjour")
    assert publishing.prepare_post(ready, "linkedin")["pending_job"]["posts"] == ["Bonjour"]


def test_prepare_instagram_browser_has_no_repo_staging(ready):
    info = publishing.prepare_post(ready, "instagram")
    assert info["transport"] == "browser"
    assert "ig_repo_found" not in info


# ---- publish → queue ----------------------------------------------------------------
def test_publish_text_queues_a_job_and_records_no_link_yet(ready):
    result = publishing.publish(ready, "linkedin", "text", "Bonjour LinkedIn")
    assert result["ok"] is True and result["queued"] is True and result["url"] == ""
    job = result["job"]
    assert job["posts"] == ["Bonjour LinkedIn"] and job["image"] == ""
    assert result["hook"]["ran"] is False             # no hook configured
    assert ready.get_link("LinkedIn") == ""           # set only once Claude reports back


def test_publish_image_queues_the_grabbed_card_with_full_text_alt(ready, tmp_path):
    result = publishing.publish(ready, "tiktok", "image", "Mon Titre")
    job = result["job"]
    assert job["image"] == str(tmp_path / publishing.image_filename(ready))
    assert "Un court texte." in job["alt_text"]


def test_publish_x_thread_via_browser_numbers_segments(ready):
    result = publishing.publish(ready, "x", "thread", "Un\n---\nDeux", {"number": True})
    assert result["job"]["posts"] == ["Un (1/2)", "Deux (2/2)"]
    assert result["job"]["mode"] == "thread"


def test_publish_thread_refused_where_unsupported(ready):
    result = publishing.publish(ready, "linkedin", "thread", "Un\n---\nDeux")
    assert result["ok"] is False and "thread" in result["error"].lower()


def test_double_queue_is_refused_until_done_cancelled_or_failed(ready):
    first = publishing.publish(ready, "threads", "text", "Un")
    again = publishing.publish(ready, "threads", "text", "Un")
    assert again["ok"] is False and "queued" in again["error"]
    browser_jobs.cancel(first["job"]["id"])
    assert publishing.publish(ready, "threads", "text", "Un")["ok"] is True


def test_browser_queue_still_enforces_guards(ready):
    assert "501" in publishing.publish(ready, "threads", "text", "x" * 501)["error"]
    assert "image" in publishing.publish(ready, "pinterest", "text", "x")["error"].lower()
    assert publishing.publish(ready, "threads", "text", "   ")["error"] == "Nothing to post."
    ready.set_link("Threads", "https://old.example")
    assert publishing.publish(ready, "threads", "text", "x")["url"] == "https://old.example"


def test_browser_queue_runs_the_hook(ready, publish_ini, monkeypatch):
    publish_ini('[Hook]\ncommand = claude --chrome "/chrome-post {id}"\n')
    monkeypatch.setattr(browser_jobs.subprocess, "Popen", lambda cmd, **kw: None)
    result = publishing.publish(ready, "medium", "text", "Long texte")
    assert result["hook"]["ran"] is True
    assert result["job"]["id"] in result["hook"]["command"]


def test_x_pinned_to_api_posts_natively(ready, publish_ini, monkeypatch):
    class Fake:
        def __init__(self, hl):
            pass

        def post(self, msg, image_local_url, alt_text, embed_url=None):
            return "https://x.com/m/status/1"
    publish_ini("[Transport]\nx = api\n")
    monkeypatch.setitem(publishing.PLATFORMS, "x",
                        Platform("x", "X / Twitter", "X/Twitter", 280, Fake,
                                 browser_url="https://x.com/compose/post",
                                 default_transport="browser"))
    result = publishing.publish(ready, "x", "text", "Salut")
    assert result == {"ok": True, "url": "https://x.com/m/status/1", "error": ""}
    assert browser_jobs.list_jobs() == []


# ---- webapi: slots, ingestion ------------------------------------------------------
def test_link_slots_badge_hide_and_keep_filled(pair, publish_ini):
    en = pair.en()
    names = lambda: {s["name"]: s for s in webapi.link_slots(en)}
    slots = names()
    assert slots["LinkedIn"]["via"] == "browser"
    assert slots["Bluesky"]["via"] == ""
    assert "Medium" not in slots                        # FR-only slot
    publish_ini("[Hidden]\nplatforms = pinterest, TikTok\n")
    en.set_link("TikTok", "https://www.tiktok.com/@m/photo/1")
    slots = names()
    assert "Pinterest" not in slots                     # hidden + empty → gone
    assert slots["TikTok"]["publish"] == ""             # hidden + filled → plain field
    assert slots["TikTok"]["url"].endswith("/photo/1")


def test_get_state_ingests_finished_jobs(pair, ready):
    api = webapi.Api(pair)
    job = publishing.publish(ready, "threads", "text", "Un")["job"]
    browser_jobs.complete(job["id"], "https://www.threads.com/@m/post/9")
    state = api.get_state("fr")
    assert {s["name"]: s["url"] for s in state["links"]}["Threads"].endswith("/post/9")
    assert api.browser_job("fr", job["id"])["status"] == "applied"


def test_api_cancel_only_touches_pending_jobs(pair, ready):
    api = webapi.Api(pair)
    job = publishing.publish(ready, "threads", "text", "Un")["job"]
    browser_jobs.complete(job["id"], "https://www.threads.com/@m/post/9")
    api.cancel_browser_job(job["id"])
    assert browser_jobs.load(job["id"])["status"] == "done"
    assert api.run_browser_hook("nope")["error"] == "No such job."
