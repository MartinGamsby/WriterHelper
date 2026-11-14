# The "browser hook": a publish routed to Claude in Chrome becomes a JSON job file in
# browser_jobs/ (CWD, git-ignored — next to the richTextArea_* captures). The
# /chrome-post Claude Code skill picks pending jobs up, posts them in the operator's
# signed-in Chrome, then reports back through this module's CLI:
#
#   python browser_jobs.py list                # pending jobs, JSON
#   python browser_jobs.py show <id>           # one job, JSON
#   python browser_jobs.py done <id> <url>     # posted — record the public URL
#   python browser_jobs.py fail <id> "<why>"   # couldn't post — record why
#   python browser_jobs.py cancel <id>
#   python browser_jobs.py clip <id>           # put the job's image on the clipboard
#
# The app never has the job's URL pushed at it: `apply_results` (called on every
# get_state pull) copies a done job's URL into the matching article's link slot.
# No Qt. See [[browser-hook]].
import json
import os
import random
import string
import subprocess
import sys
import time

import publish_config

JOBS_DIR = "browser_jobs"

PENDING, DONE, FAILED, APPLIED, CANCELLED = (
    "pending", "done", "failed", "applied", "cancelled")


# ========================================================================================
def _path(job_id):
    return os.path.join(JOBS_DIR, "%s.json" % job_id)


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def save(job):
    os.makedirs(JOBS_DIR, exist_ok=True)
    tmp = _path(job["id"]) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(job, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _path(job["id"]))   # atomic: the app may read while the skill writes


def load(job_id):
    """The job dict, or None when unknown. Ids are validated so a CLI argument can't
    walk out of JOBS_DIR."""
    if not job_id or any(c in job_id for c in "/\\.") or not os.path.isfile(_path(job_id)):
        return None
    with open(_path(job_id), encoding="utf-8") as f:
        return json.load(f)


def list_jobs(status=None):
    """All jobs (oldest first), optionally filtered by status."""
    if not os.path.isdir(JOBS_DIR):
        return []
    jobs = []
    for name in sorted(os.listdir(JOBS_DIR)):
        if name.endswith(".json"):
            job = load(name[:-5])
            if job and (status is None or job["status"] == status):
                jobs.append(job)
    return jobs


# ========================================================================================
def _article_ref(article):
    return {"hl": article.hl, "slug": article.get_slug(),
            "translation_key": article.get_translation_key(),
            "title": article.title}


def _matches(job, article):
    """Does `job` belong to `article`? The sticky translationKey survives a title edit
    (which changes the slug) between queueing and completion; the slug is the
    fallback for an article without a key yet."""
    ref = job.get("article", {})
    if ref.get("hl") != article.hl:
        return False
    key = article.get_translation_key()
    if key and ref.get("translation_key"):
        return ref["translation_key"] == key
    return ref.get("slug") == article.get_slug()


def pending_for(article, platform):
    """The still-pending job for this article + platform, or None (the double-post
    guard while Claude hasn't reported back yet)."""
    for job in list_jobs(PENDING):
        if job["platform"] == platform.key and _matches(job, article):
            return job
    return None


# ========================================================================================
def create(article, platform, mode, posts, image="", alt_text=""):
    """Queue one post (or a thread: several `posts`) for Claude in Chrome and return
    the job. `image` is a local file (stored absolute: the skill may run elsewhere
    than the app's CWD) attached to the first post."""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    suffix = "".join(random.choice(string.ascii_lowercase) for _ in range(4))
    job = {
        "id": "%s-%s-%s-%s" % (stamp, platform.key, article.hl, suffix),
        "status": PENDING,
        "created": _now(),
        "platform": platform.key,
        "label": platform.label,
        "compose_url": platform.browser_url,
        "hl": article.hl,
        "account": publish_config.account_hint(platform.key, article.hl),
        "mode": mode,
        "posts": list(posts),
        "title": article.title,
        "image": os.path.abspath(image) if image else "",
        "alt_text": alt_text,
        "link": article.get_post_url(),
        "link_slot": platform.link_name,
        "max_length": platform.max_length,
        "article": _article_ref(article),
        "url": "",
        "error": "",
    }
    if platform.key == "pinterest":
        job["board"] = publish_config.pinterest_board(article.hl)
    save(job)
    return job


def _finish(job_id, status, **fields):
    job = load(job_id)
    if job is None:
        raise KeyError("No such job: %s" % job_id)
    job.update(fields, status=status, finished=_now())
    save(job)
    return job


def complete(job_id, url):
    if not url.startswith(("http://", "https://")):
        raise ValueError("Not a URL: %r" % url)
    return _finish(job_id, DONE, url=url, error="")


def fail(job_id, error):
    return _finish(job_id, FAILED, error=error)


def cancel(job_id):
    return _finish(job_id, CANCELLED)


# ========================================================================================
def apply_results(article):
    """Copy every finished-but-unapplied job URL for `article` into its link slot
    (re-saving the footer) and mark the job applied. A slot that meanwhile got a URL
    by hand is left alone. Returns the jobs applied."""
    applied = []
    for job in list_jobs(DONE):
        if not _matches(job, article):
            continue
        if not article.get_link(job["link_slot"]):
            article.set_link(job["link_slot"], job["url"])
        job.update(status=APPLIED, applied=_now())
        save(job)
        applied.append(job)
    return applied


# ========================================================================================
def run_hook(job):
    """Start the operator's configured hook command for a new job (typically an
    interactive `claude --chrome "/chrome-post {id}"` in a new console). Fire and
    forget: the result arrives through `done`/`fail`. Returns what happened."""
    template = publish_config.hook_command()
    if not template:
        return {"ran": False, "command": "", "error": ""}
    command = template.replace("{id}", job["id"]).replace(
        "{job}", os.path.abspath(_path(job["id"])))
    try:
        flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        # shell=True: the command comes from the operator's own settings file, and a
        # shell resolves `claude`'s .cmd shim on Windows.
        subprocess.Popen(command, shell=True, creationflags=flags)
    except Exception as exc:
        return {"ran": False, "command": command, "error": str(exc)}
    return {"ran": True, "command": command, "error": ""}


def clipboard_command(path):
    """The OS command that puts an image file on the clipboard (the paste fallback when
    the browser tools can't set a file input), or None when unsupported."""
    if sys.platform.startswith("win"):
        quoted = path.replace("'", "''")
        script = ("Add-Type -AssemblyName System.Windows.Forms; "
                  "Add-Type -AssemblyName System.Drawing; "
                  "[System.Windows.Forms.Clipboard]::SetImage("
                  "[System.Drawing.Image]::FromFile('%s'))" % quoted)
        return ["powershell", "-NoProfile", "-STA", "-Command", script]
    if sys.platform == "darwin":
        kind = "JPEG picture" if path.lower().endswith((".jpg", ".jpeg")) else "«class PNGf»"
        return ["osascript", "-e",
                'set the clipboard to (read (POSIX file "%s") as %s)' % (path, kind)]
    mime = "image/jpeg" if path.lower().endswith((".jpg", ".jpeg")) else "image/png"
    return ["xclip", "-selection", "clipboard", "-t", mime, "-i", path]


# ========================================================================================
def _cli(argv):
    usage = ("usage: browser_jobs.py list | show <id> | done <id> <url> | "
             "fail <id> <why> | cancel <id> | clip <id>")
    if not argv:
        print(usage, file=sys.stderr)
        return 2
    cmd, args = argv[0], argv[1:]
    try:
        if cmd == "list":
            print(json.dumps(list_jobs(PENDING), ensure_ascii=False, indent=2))
            return 0
        if not args:
            print(usage, file=sys.stderr)
            return 2
        if cmd == "show":
            job = load(args[0])
            if job is None:
                raise KeyError("No such job: %s" % args[0])
            print(json.dumps(job, ensure_ascii=False, indent=2))
        elif cmd == "done" and len(args) == 2:
            complete(args[0], args[1])
            print("Recorded %s → %s (the app links it on its next refresh)."
                  % (args[0], args[1]))
        elif cmd == "fail" and len(args) >= 2:
            fail(args[0], " ".join(args[1:]))
            print("Marked %s failed." % args[0])
        elif cmd == "cancel":
            cancel(args[0])
            print("Cancelled %s." % args[0])
        elif cmd == "clip":
            job = load(args[0])
            if job is None or not job.get("image"):
                raise KeyError("Job %s has no image." % args[0])
            subprocess.run(clipboard_command(job["image"]), check=True)
            print("Image on the clipboard: %s" % job["image"])
        else:
            print(usage, file=sys.stderr)
            return 2
    except (KeyError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        print("error: %s" % (exc.args[0] if exc.args else exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
