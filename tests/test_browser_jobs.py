import json
import os
import sys

import pytest

import browser_jobs
import publishing


# ========================================================================================
def _queue(article, platform_key="linkedin", posts=("Bonjour",), image=""):
    p = publishing.PLATFORMS[platform_key]
    return browser_jobs.create(article, p, "text", list(posts), image, "alt")


def test_create_writes_a_pending_job_with_everything_the_skill_needs(fr, publish_ini):
    publish_ini("[Accounts]\nlinkedin_fr = @martin\n")
    fr.set_title("Mon Titre")
    job = _queue(fr)
    on_disk = json.load(open(os.path.join(browser_jobs.JOBS_DIR, job["id"] + ".json"),
                             encoding="utf-8"))
    assert on_disk == job
    assert job["status"] == "pending"
    assert job["platform"] == "linkedin" and job["hl"] == "fr"
    assert job["compose_url"].startswith("https://www.linkedin.com/")
    assert job["posts"] == ["Bonjour"]
    assert job["link_slot"] == "LinkedIn"
    assert job["account"] == "martin"          # "@" stripped
    assert job["link"] == fr.get_post_url()
    assert job["article"]["slug"] == "mon-titre"


def test_image_path_is_stored_absolute(fr, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "card.jpg").write_bytes(b"jpg")
    job = _queue(fr, image="card.jpg")
    assert job["image"] == str(tmp_path / "card.jpg")


def test_pinterest_job_carries_the_board(fr, publish_ini):
    publish_ini("[Pinterest]\nboard_fr = Blogue\n")
    job = _queue(fr, "pinterest")
    assert job["board"] == "Blogue"


def test_pending_for_matches_platform_and_article(fr, pair):
    fr.set_title("Titre")
    _queue(fr, "linkedin")
    assert browser_jobs.pending_for(fr, publishing.PLATFORMS["linkedin"])
    assert browser_jobs.pending_for(fr, publishing.PLATFORMS["threads"]) is None
    assert browser_jobs.pending_for(pair.en(), publishing.PLATFORMS["linkedin"]) is None


def test_complete_then_apply_sets_the_link_slot(fr):
    fr.set_title("Titre")
    fr.set_facets(["dev"])
    job = _queue(fr, "threads")
    browser_jobs.complete(job["id"], "https://www.threads.com/@m/post/ABC")
    applied = browser_jobs.apply_results(fr)
    assert [j["id"] for j in applied] == [job["id"]]
    assert fr.get_link("Threads") == "https://www.threads.com/@m/post/ABC"
    assert browser_jobs.load(job["id"])["status"] == "applied"
    assert browser_jobs.apply_results(fr) == []          # idempotent


def test_apply_survives_a_title_edit_via_translation_key(fr):
    fr.set_title("Premier titre")
    fr.set_facets(["dev"])
    job = _queue(fr, "threads")
    fr.set_title("Titre corrigé")                       # slug changes, key is sticky
    browser_jobs.complete(job["id"], "https://www.threads.com/@m/post/XYZ")
    browser_jobs.apply_results(fr)
    assert fr.get_link("Threads") == "https://www.threads.com/@m/post/XYZ"


def test_apply_ignores_other_articles_and_keeps_a_hand_set_link(fr, pair):
    fr.set_title("Titre")
    job = _queue(fr, "threads")
    browser_jobs.complete(job["id"], "https://www.threads.com/@m/post/1")
    assert browser_jobs.apply_results(pair.en()) == []   # other language: untouched
    fr.set_link("Threads", "https://by-hand.example")
    browser_jobs.apply_results(fr)
    assert fr.get_link("Threads") == "https://by-hand.example"


def test_complete_rejects_a_non_url_and_unknown_ids(fr):
    job = _queue(fr)
    with pytest.raises(ValueError):
        browser_jobs.complete(job["id"], "posted!")
    with pytest.raises(KeyError):
        browser_jobs.complete("nope", "https://x.com/a")


def test_load_refuses_path_traversal(fr):
    assert browser_jobs.load("../settings_fr") is None
    assert browser_jobs.load("a/b") is None


def test_fail_and_cancel_clear_the_pending_guard(fr):
    a = _queue(fr, "linkedin")
    b = _queue(fr, "threads")
    browser_jobs.fail(a["id"], "Not signed in")
    browser_jobs.cancel(b["id"])
    assert browser_jobs.load(a["id"])["error"] == "Not signed in"
    assert browser_jobs.list_jobs("pending") == []


# ========================================================================================
def test_run_hook_without_a_command_does_nothing(fr, monkeypatch):
    monkeypatch.setattr(browser_jobs.subprocess, "Popen",
                        lambda *a, **k: pytest.fail("must not run"))
    assert browser_jobs.run_hook(_queue(fr)) == {"ran": False, "command": "", "error": ""}


def test_run_hook_substitutes_id_and_job_path(fr, publish_ini, monkeypatch):
    publish_ini('[Hook]\ncommand = claude --chrome "/chrome-post {id}" # {job}\n')
    calls = []
    monkeypatch.setattr(browser_jobs.subprocess, "Popen",
                        lambda cmd, **kw: calls.append((cmd, kw)))
    job = _queue(fr)
    result = browser_jobs.run_hook(job)
    assert result["ran"] is True
    cmd, kw = calls[0]
    assert '"/chrome-post %s"' % job["id"] in cmd
    assert os.path.abspath(os.path.join(browser_jobs.JOBS_DIR, job["id"] + ".json")) in cmd
    assert kw["shell"] is True


def test_run_hook_reports_a_launch_failure(fr, publish_ini, monkeypatch):
    publish_ini("[Hook]\ncommand = nope\n")

    def boom(*a, **k):
        raise OSError("not found")
    monkeypatch.setattr(browser_jobs.subprocess, "Popen", boom)
    result = browser_jobs.run_hook(_queue(fr))
    assert result["ran"] is False and "not found" in result["error"]


@pytest.mark.parametrize("platform,head", [("win32", "powershell"),
                                           ("darwin", "osascript"),
                                           ("linux", "xclip")])
def test_clipboard_command_per_os(monkeypatch, platform, head):
    monkeypatch.setattr(sys, "platform", platform)
    cmd = browser_jobs.clipboard_command("C:/x/it's.jpg")
    assert cmd[0] == head
    if head == "powershell":
        assert "it''s.jpg" in cmd[-1]     # single quote escaped for PowerShell


# ========================================================================================
def test_cli_list_done_show(fr, capsys):
    job = _queue(fr, "threads")
    assert browser_jobs._cli(["list"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["id"] == job["id"]
    assert browser_jobs._cli(["done", job["id"], "https://www.threads.com/p/1"]) == 0
    capsys.readouterr()
    assert browser_jobs._cli(["show", job["id"]]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "done"
    assert browser_jobs._cli(["list"]) == 0
    assert json.loads(capsys.readouterr().out) == []


def test_cli_errors_are_reported_not_raised(fr, capsys):
    assert browser_jobs._cli([]) == 2
    assert browser_jobs._cli(["done", "nope", "https://x"]) == 1
    assert "No such job" in capsys.readouterr().err
    job = _queue(fr)
    assert browser_jobs._cli(["fail", job["id"], "Login", "wall"]) == 0
    assert browser_jobs.load(job["id"])["error"] == "Login wall"
    assert browser_jobs._cli(["clip", job["id"]]) == 1    # no image on this job
