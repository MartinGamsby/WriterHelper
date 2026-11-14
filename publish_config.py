# Operator knobs for publishing, read from the git-ignored settings_publish.ini (CWD,
# like every other settings_*.ini). Every key is optional: a missing file or key
# falls back to the defaults baked into platforms.PLATFORMS. Not secret (no tokens
# live here) — see [[browser-hook]] for the full reference.
#
#   [Transport]          ; per platform key: browser | api (only where both exist)
#   x = api
#   [Hidden]
#   platforms = pinterest, tiktok
#   [Hook]
#   command = claude --chrome "/chrome-post {id}"
#   [Accounts]           ; expected signed-in handle, per <platform>_<hl> or <platform>
#   x_en = Martin_Gamsby
#   [Pinterest]
#   board_fr = Blogue
import configparser
import os

CONFIG_FILE = "settings_publish.ini"


def _load():
    """A fresh read every call: the file is tiny and the operator may edit it while
    the app runs (no restart needed)."""
    cfg = configparser.ConfigParser()
    if os.path.isfile(CONFIG_FILE):
        cfg.read(CONFIG_FILE, encoding="utf-8")
    return cfg


def _get(section, key, default=""):
    cfg = _load()
    if cfg.has_section(section):
        return cfg[section].get(key, default).strip()
    return default


def transport_override(platform_key) -> str:
    """"browser" / "api" when the operator pinned one, else ""."""
    return _get("Transport", platform_key).lower()


def hidden_platforms() -> set:
    raw = _get("Hidden", "platforms")
    return {p.strip().lower() for p in raw.split(",") if p.strip()}


def hook_command() -> str:
    """The shell command run after a browser job is queued ("" = don't run anything;
    the popup shows the /chrome-post command to type instead). `{id}` and `{job}`
    (the job file's absolute path) are substituted."""
    return _get("Hook", "command")


def account_hint(platform_key, hl) -> str:
    """The handle/name the browser session is expected to be signed in as, so the
    skill can refuse to post a FR article from the EN account. "" = not pinned."""
    return (_get("Accounts", "%s_%s" % (platform_key, hl))
            or _get("Accounts", platform_key)).lstrip("@")


def pinterest_board(hl) -> str:
    return _get("Pinterest", "board_%s" % hl) or _get("Pinterest", "board")
