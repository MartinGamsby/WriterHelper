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
                 branch="main", commit_rc=0, push_rc=0, push_stderr="",
                 tracked=True, diff_rc=0, ahead="0"):
        self.remote, self.branch = remote, branch
        self.commit_rc, self.push_rc, self.push_stderr = commit_rc, push_rc, push_stderr
        self.tracked, self.diff_rc, self.ahead = tracked, diff_rc, ahead
        self.calls = []

    def __call__(self, repo, *args, timeout=60):
        self.calls.append(args)
        if args[:2] == ("remote", "get-url"):
            return _Result(stdout=self.remote)
        if args[:1] == ("rev-parse",):
            return _Result(stdout=self.branch)
        if args[:1] == ("ls-files",):      # status: tracked?
            return _Result(returncode=0 if self.tracked else 1)
        if args[:1] == ("diff",):          # status: unmodified vs HEAD?
            return _Result(returncode=self.diff_rc)
        if args[:1] == ("rev-list",):      # status: commits ahead of origin
            return _Result(stdout=self.ahead)
        if args[:1] == ("commit",):
            return _Result(returncode=self.commit_rc,
                           stdout="nothing to commit, working tree clean"
                           if self.commit_rc else "")
        if args[:1] == ("push",):
            return _Result(returncode=self.push_rc, stderr=self.push_stderr)
        return _Result()   # add, etc.

    def verbs(self):
        return [c[0] for c in self.calls]


def _staged_pair(tmp_path, same=True):
    """A site repo with public/assets/ig/x.fr.jpg + a local grabbed card (identical or
    not) so image_status's byte-compare is exercised on real files."""
    ig = tmp_path / "site" / "public" / "assets" / "ig"
    ig.mkdir(parents=True)
    (ig / "x.fr.jpg").write_bytes(b"IMGBYTES")
    img = tmp_path / "richTextArea_x_fr1.jpg"
    img.write_bytes(b"IMGBYTES" if same else b"DIFFERENT")
    return str(tmp_path / "site"), str(img)


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


# ========================================================================================
# image_status — lets the popup skip step 1 on a reopen when the image is already pushed.
def test_image_status_pushed_when_identical_and_committed(tmp_path, monkeypatch):
    monkeypatch.setattr(site_push, "_git", FakeGit())
    repo, img = _staged_pair(tmp_path, same=True)
    st = site_push.image_status(repo, "x.fr.jpg", img)
    assert st["pushed"] is True
    assert st["public_url"].endswith("/public/assets/ig/x.fr.jpg")


def test_image_status_not_pushed_when_dest_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(site_push, "_git", FakeGit())
    repo = tmp_path / "site"
    repo.mkdir()
    img = tmp_path / "card.jpg"
    img.write_bytes(b"IMGBYTES")
    assert site_push.image_status(str(repo), "x.fr.jpg", str(img))["pushed"] is False


def test_image_status_not_pushed_when_bytes_differ(tmp_path, monkeypatch):
    # A re-grabbed (changed) card must NOT be mistaken for the already-pushed one.
    monkeypatch.setattr(site_push, "_git", FakeGit())
    repo, img = _staged_pair(tmp_path, same=False)
    assert site_push.image_status(repo, "x.fr.jpg", img)["pushed"] is False


def test_image_status_not_pushed_when_commit_is_unpushed(tmp_path, monkeypatch):
    # Identical + committed, but the commit is ahead of origin → not actually public yet.
    monkeypatch.setattr(site_push, "_git", FakeGit(ahead="1"))
    repo, img = _staged_pair(tmp_path, same=True)
    assert site_push.image_status(repo, "x.fr.jpg", img)["pushed"] is False


def test_image_status_not_pushed_when_untracked(tmp_path, monkeypatch):
    monkeypatch.setattr(site_push, "_git", FakeGit(tracked=False))
    repo, img = _staged_pair(tmp_path, same=True)
    assert site_push.image_status(repo, "x.fr.jpg", img)["pushed"] is False
