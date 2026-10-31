# Stage + git-push one image into the sibling martingamsby.com checkout so a public
# raw.githubusercontent.com URL exists for it. Instagram's Content Publishing API
# fetches the image server-side, so it must be reachable on the web BEFORE the post
# call ([[instagram-adapter]]); a raw URL is public the moment it's pushed, with no
# GitHub Actions deploy wait. Pure helper: copy the file into public/assets/ig/,
# commit JUST that file, push the branch, and build the raw URL from `origin`.
import filecmp
import os
import re
import shutil
import subprocess

# Where IG source images live inside the site repo — separate from the site's own
# localize output (assets/posts/*.webp). Astro serves public/ verbatim, and the file
# is reachable via raw.githubusercontent.com regardless of any deploy.
IG_ASSET_SUBDIR = os.path.join("public", "assets", "ig")
_GIT_TIMEOUT = 60


# ====================================================================================
def _git(repo, *args, timeout=_GIT_TIMEOUT):
    """Run a git subcommand in `repo`; return the CompletedProcess. Never raises on a
    non-zero exit — callers inspect returncode / stderr and report it to the UI."""
    return subprocess.run(["git", "-C", repo, *args],
                          capture_output=True, text=True, timeout=timeout)


# ====================================================================================
def repo_slug(repo):
    """`owner/name` parsed from the `origin` remote URL (https or ssh form), or None."""
    r = _git(repo, "remote", "get-url", "origin")
    if r.returncode != 0:
        return None
    m = re.search(r"github\.com[:/]+([^/]+?/[^/]+?)(?:\.git)?/?\s*$", r.stdout.strip())
    return m.group(1) if m else None


def current_branch(repo):
    """The checked-out branch name, or "" if it can't be read (e.g. detached HEAD)."""
    r = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    return r.stdout.strip() if r.returncode == 0 else ""


def raw_url(repo, rel_path):
    """The public raw.githubusercontent.com URL a file at `rel_path` (repo-relative)
    will have once pushed, or None if the origin remote can't be parsed."""
    slug = repo_slug(repo)
    if not slug:
        return None
    branch = current_branch(repo) or "main"
    return "https://raw.githubusercontent.com/%s/%s/%s" % (
        slug, branch, rel_path.replace(os.sep, "/"))


# ====================================================================================
def _is_pushed(repo, rel_path):
    """True if `rel_path` is tracked, matches HEAD (committed, no working-tree change),
    and isn't an unpushed local commit. Read-only. The origin compare is best-effort: if
    the remote-tracking ref is missing it falls back to tracked+committed."""
    if _git(repo, "ls-files", "--error-unmatch", "--", rel_path).returncode != 0:
        return False
    if _git(repo, "diff", "--quiet", "HEAD", "--", rel_path).returncode != 0:
        return False
    branch = current_branch(repo)
    if branch:
        ahead = _git(repo, "rev-list", "--count", "origin/%s..HEAD" % branch, "--", rel_path)
        if ahead.returncode == 0:
            return ahead.stdout.strip() in ("", "0")
    return True


def image_status(repo, dest_name, local_image) -> dict:
    """Read-only: is `local_image` already staged+pushed at public/assets/ig/<dest_name>?
    Returns `{pushed, public_url}`. `pushed` requires the dest file to exist, be
    byte-identical to the current grabbed card (so a stale or changed card isn't mistaken
    for the live one), and be committed + pushed. Lets the IG popup skip step 1 on a
    reopen instead of forcing a redundant re-push ([[instagram-adapter]])."""
    rel_path = os.path.join(IG_ASSET_SUBDIR, dest_name)
    public_url = raw_url(repo, rel_path) or ""
    dest_abs = os.path.join(repo, rel_path)
    if not (os.path.isfile(local_image) and os.path.isfile(dest_abs)
            and filecmp.cmp(local_image, dest_abs, shallow=False)):
        return {"pushed": False, "public_url": public_url}
    return {"pushed": _is_pushed(repo, rel_path), "public_url": public_url}


# ====================================================================================
def stage_and_push_image(repo, local_image, dest_name, commit_msg) -> dict:
    """Copy `local_image` into `repo`'s public/assets/ig/<dest_name>, commit JUST that
    file, push the current branch, and return the public raw URL it now lives at.

    Returns `{ok, public_url, log, error}`; `log` is a human-readable step list for the
    popup. Explicit and best-effort: any git failure comes back as ok=False + the git
    stderr so the UI can show it (nothing is posted to IG until this succeeds). The push
    sends the whole branch, so any other already-committed work goes up with it — the
    log makes that visible."""
    log = []
    if not os.path.isfile(local_image):
        return {"ok": False, "public_url": "", "log": log,
                "error": "%s not found — Grab the image card first." % local_image}

    rel_path = os.path.join(IG_ASSET_SUBDIR, dest_name)
    public_url = raw_url(repo, rel_path)
    if not public_url:
        return {"ok": False, "public_url": "", "log": log,
                "error": "Couldn't read the site repo's GitHub 'origin' remote — is %s "
                         "a GitHub clone?" % repo}

    dest_abs = os.path.join(repo, rel_path)
    try:
        os.makedirs(os.path.dirname(dest_abs), exist_ok=True)
        shutil.copyfile(local_image, dest_abs)
        log.append("Copied image -> %s" % rel_path.replace(os.sep, "/"))

        add = _git(repo, "add", "--", rel_path)
        if add.returncode != 0:
            return _git_fail(log, "git add", add)

        commit = _git(repo, "commit", "-m", commit_msg, "--", rel_path)
        if commit.returncode == 0:
            log.append("Committed: %s" % commit_msg)
        elif "nothing to commit" in (commit.stdout + commit.stderr).lower():
            log.append("No change to commit (image already committed in a prior push)")
        else:
            return _git_fail(log, "git commit", commit)

        push = _git(repo, "push", "origin", "HEAD")
        if push.returncode != 0:
            return _git_fail(log, "git push", push)
        log.append("Pushed to origin — image is now public")
    except (OSError, subprocess.SubprocessError) as err:
        return {"ok": False, "public_url": "", "log": log,
                "error": "Image push failed: %s" % err}

    return {"ok": True, "public_url": public_url, "log": log, "error": ""}


def _git_fail(log, step, proc):
    return {"ok": False, "public_url": "", "log": log,
            "error": "%s failed: %s" % (step, (proc.stderr or proc.stdout).strip())}
