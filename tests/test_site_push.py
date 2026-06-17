import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import site_push  # noqa: E402


# ========================================================================================
class _Result:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class FakeGit:
    """Records git subcommands and returns canned results — no real repo needed."""
    def __init__(self, remote="https://github.com/MartinGamsby/martingamsby.com.git",
                 branch="main", commit_rc=0, push_rc=0, push_stderr=""):
        self.remote, self.branch = remote, branch
        self.commit_rc, self.push_rc, self.push_stderr = commit_rc, push_rc, push_stderr
        self.calls = []

    def __call__(self, repo, *args, timeout=60):
        self.calls.append(args)
        if args[:2] == ("remote", "get-url"):
            return _Result(stdout=self.remote)
        if args[:1] == ("rev-parse",):
            return _Result(stdout=self.branch)
        if args[:1] == ("commit",):
            return _Result(returncode=self.commit_rc,
                           stdout="nothing to commit, working tree clean"
                           if self.commit_rc else "")
        if args[:1] == ("push",):
            return _Result(returncode=self.push_rc, stderr=self.push_stderr)
        return _Result()   # add, etc.

    def verbs(self):
        return [c[0] for c in self.calls]


# ========================================================================================
def test_repo_slug_parses_https(monkeypatch):
    monkeypatch.setattr(site_push, "_git", FakeGit())
    assert site_push.repo_slug("/repo") == "MartinGamsby/martingamsby.com"


def test_repo_slug_parses_ssh(monkeypatch):
    monkeypatch.setattr(site_push, "_git",
                        FakeGit(remote="git@github.com:MartinGamsby/martingamsby.com.git"))
    assert site_push.repo_slug("/repo") == "MartinGamsby/martingamsby.com"


def test_raw_url_built_from_remote_and_branch(monkeypatch):
    monkeypatch.setattr(site_push, "_git", FakeGit(branch="main"))
    rel = os.path.join("public", "assets", "ig", "x.fr.jpg")
    assert site_push.raw_url("/repo", rel) == (
        "https://raw.githubusercontent.com/MartinGamsby/martingamsby.com/main/"
        "public/assets/ig/x.fr.jpg")


def test_stage_copies_commits_and_pushes(tmp_path, monkeypatch):
    repo = tmp_path / "site"
    repo.mkdir()
    img = tmp_path / "card.jpg"
    img.write_bytes(b"jpgbytes")
    fake = FakeGit()
    monkeypatch.setattr(site_push, "_git", fake)

    res = site_push.stage_and_push_image(str(repo), str(img), "my-slug.fr.jpg", "msg")
    assert res["ok"] is True
    assert res["public_url"].endswith("/public/assets/ig/my-slug.fr.jpg")
    # The image was copied into the repo's public assets folder.
    assert (repo / "public" / "assets" / "ig" / "my-slug.fr.jpg").read_bytes() == b"jpgbytes"
    # add + commit + push all happened.
    for verb in ("add", "commit", "push"):
        assert verb in fake.verbs()


def test_stage_missing_image_is_error(tmp_path, monkeypatch):
    monkeypatch.setattr(site_push, "_git", FakeGit())
    res = site_push.stage_and_push_image(str(tmp_path), str(tmp_path / "nope.jpg"),
                                         "x.fr.jpg", "msg")
    assert res["ok"] is False
    assert "not found" in res["error"]


def test_stage_push_failure_surfaces_git_stderr(tmp_path, monkeypatch):
    repo = tmp_path / "site"
    repo.mkdir()
    img = tmp_path / "card.jpg"
    img.write_bytes(b"x")
    monkeypatch.setattr(site_push, "_git", FakeGit(push_rc=1, push_stderr="rejected: auth"))
    res = site_push.stage_and_push_image(str(repo), str(img), "x.fr.jpg", "msg")
    assert res["ok"] is False
    assert "push failed" in res["error"].lower()
    assert "rejected: auth" in res["error"]


def test_stage_nothing_to_commit_is_not_fatal(tmp_path, monkeypatch):
    # Re-pushing an unchanged image: commit says "nothing to commit" but the URL is
    # still valid, so the step succeeds.
    repo = tmp_path / "site"
    repo.mkdir()
    img = tmp_path / "card.jpg"
    img.write_bytes(b"x")
    monkeypatch.setattr(site_push, "_git", FakeGit(commit_rc=1))
    res = site_push.stage_and_push_image(str(repo), str(img), "x.fr.jpg", "msg")
    assert res["ok"] is True


def test_stage_no_github_remote_is_error(tmp_path, monkeypatch):
    repo = tmp_path / "site"
    repo.mkdir()
    img = tmp_path / "card.jpg"
    img.write_bytes(b"x")
    monkeypatch.setattr(site_push, "_git", FakeGit(remote="https://gitlab.com/x/y.git"))
    res = site_push.stage_and_push_image(str(repo), str(img), "x.fr.jpg", "msg")
    assert res["ok"] is False
    assert "origin" in res["error"].lower()
