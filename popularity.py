"""Popularity tracking for the bilingual blog (see [[popularity-tracking]]).

Every published article records *where* it was posted in its footer link slots
([[link-slots]]). This module turns those slots into a worklist of URLs to read
engagement numbers from, and keeps an append-only ledger of dated snapshots so
month-over-month trends fall out.

The numbers themselves are gathered by the `/popularity` skill — Bluesky via the
scripted public API here (`bsky_metrics`, no auth, no key), and the rest read from
the operator's logged-in browser via Claude-for-Chrome. This module is the pure,
testable spine: enumerate links, store readings, summarize movers. It never touches
the Astro post files or the wiki — the ledger lives in the WriterHelper repo.

    python popularity.py worklist            # JSON: every readable post link
    python popularity.py bsky <bsky-url>     # JSON: scripted Bluesky counts
    python popularity.py record --date D ... # append readings to the ledger
    python popularity.py summary             # ranked readout + deltas vs last run
"""
import configparser
import json
import os
import re
import sys

import requests
import yaml

import serializers  # footer parser is the single source of truth for the tricky
                    # multi-line / trailing-paren link format ([[link-slots]]).

DEFAULT_LEDGER = "popularity.json"

# Engagement-bearing slots — mirrors webapi.LINK_SLOTS, MINUS the reference slots
# ("Source", "Based on"/"Basé sur"): those point at someone else's page, not at a
# post of ours whose reception we measure.
ENGAGEMENT_PLATFORMS = {
    "Medium", "Typeshare", "X/Twitter", "LinkedIn", "Facebook",
    "Instagram", "Bluesky", "YouTube", "YouTube Shorts",
}

# The single number used to rank a platform's posts and headline its movers. Each
# reading's `metrics` dict may carry more (reposts, replies, views…); this is just
# the ranking key, with a sum-of-values fallback when it's absent.
PRIMARY_METRIC = {
    "X/Twitter": "likes",
    "Bluesky": "likes",
    "YouTube": "views",
    "YouTube Shorts": "views",
    "Medium": "claps",
    "LinkedIn": "reactions",
    "Facebook": "reactions",
    "Instagram": "likes",
    "Typeshare": "likes",
}

_FM_RE = re.compile(r'^\s*---\s*\n(.*?)\n---\s*\n', re.S)


# ========================================================================================
# Worklist: every (article, platform, url) we can read a number from
# ========================================================================================
def _is_url(target):
    return target.strip().lower().startswith(("http://", "https://"))


def _split(text):
    """(frontmatter dict, footer text) for one Astro post. Footer parsing is delegated
    to serializers so multi-line / legacy slots are handled identically to load."""
    m = _FM_RE.match(text)
    header = (yaml.safe_load(m.group(1)) if m else None) or {}
    _, footer = serializers._astro_body_footer(text)
    return header, footer


def links_in_file(path, hl):
    """Yield one worklist row per readable engagement slot in the file at `path`.
    Skips reference slots and any slot whose target isn't an http(s) URL (legacy
    Bluesky slots hold post *text*, not a link — nothing to visit)."""
    with open(path, mode="r", encoding="utf-8") as fh:
        text = fh.read()
    header, footer = _split(text)
    key = str(header.get("translationKey") or os.path.basename(path)[:-3])
    title = str(header.get("title") or "")
    date = str(header.get("date") or os.path.basename(path)[:10])
    for slot, target in serializers._iter_footer_links(footer):
        if slot in ENGAGEMENT_PLATFORMS and _is_url(target):
            yield {"key": key, "hl": hl, "title": title, "date": date,
                   "platform": slot, "url": target.strip()}


def collect_worklist(fr_folder, en_folder, platforms=None, hls=None):
    """Every readable post link across both languages, sorted for stable output.
    `platforms`/`hls` (iterables) scope a single run so a 400-link sweep can be
    chunked across sessions ("X-EN today, Typeshare tomorrow") — resumable because
    same-day re-records merge ([[popularity-tracking]])."""
    platforms = set(platforms) if platforms else None
    hls = set(hls) if hls else None
    rows = []
    for hl, folder in (("fr", fr_folder), ("en", en_folder)):
        if (hls and hl not in hls) or not folder or not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            if name.endswith(".md"):
                rows.extend(links_in_file(os.path.join(folder, name), hl))
    if platforms:
        rows = [r for r in rows if r["platform"] in platforms]
    rows.sort(key=lambda r: (r["platform"], r["hl"], r["date"], r["key"]))
    return rows


def _configured_folder(hl, config_dir="."):
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(config_dir, "settings_%s.ini" % hl))
    return cfg["Paths"]["Posts"]


# ========================================================================================
# Bluesky: scripted public reads (no auth, no API key)
# ========================================================================================
_BSKY_API = "https://public.api.bsky.app/xrpc"
_BSKY_POST_RE = re.compile(r'/profile/([^/]+)/post/([^/?#]+)')


def _bsky_did(actor):
    if actor.startswith("did:"):
        return actor
    r = requests.get(_BSKY_API + "/app.bsky.actor.getProfile",
                     params={"actor": actor}, timeout=20)
    r.raise_for_status()
    return r.json()["did"]


def bsky_metrics(url):
    """{likes, reposts, replies, quotes} for a bsky.app post URL via the public
    AppView. Raises on a malformed URL or network error so the skill can log a gap."""
    m = _BSKY_POST_RE.search(url)
    if not m:
        raise ValueError("not a bsky.app post URL: %s" % url)
    at_uri = "at://%s/app.bsky.feed.post/%s" % (_bsky_did(m.group(1)), m.group(2))
    r = requests.get(_BSKY_API + "/app.bsky.feed.getPostThread",
                     params={"uri": at_uri, "depth": 0}, timeout=20)
    r.raise_for_status()
    post = r.json()["thread"]["post"]
    return {"likes": post.get("likeCount", 0), "reposts": post.get("repostCount", 0),
            "replies": post.get("replyCount", 0), "quotes": post.get("quoteCount", 0)}


# ========================================================================================
# Ledger: append-only dated snapshots
# ========================================================================================
def load_ledger(path=DEFAULT_LEDGER):
    if not os.path.isfile(path):
        return {"snapshots": []}
    with open(path, mode="r", encoding="utf-8-sig") as fh:  # tolerate a BOM
        return json.load(fh)


def save_ledger(ledger, path=DEFAULT_LEDGER):
    with open(path, mode="w", encoding="utf-8") as fh:
        json.dump(ledger, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def _reading_id(r):
    return (r["key"], r["hl"], r["platform"])


def record_snapshot(ledger, date, readings):
    """Add/refresh the snapshot for `date`. Re-running on the same day MERGES by
    (key, hl, platform) — a freshly-read post overwrites its earlier reading rather
    than duplicating it — so the skill is safe to resume mid-sweep."""
    snap = next((s for s in ledger["snapshots"] if s["date"] == date), None)
    if snap is None:
        snap = {"date": date, "readings": []}
        ledger["snapshots"].append(snap)
        ledger["snapshots"].sort(key=lambda s: s["date"])
    by_id = {_reading_id(r): r for r in snap["readings"]}
    for r in readings:
        by_id[_reading_id(r)] = r
    snap["readings"] = sorted(by_id.values(), key=_reading_id)
    return ledger


# ========================================================================================
# Summary: rank + movers vs the previous snapshot
# ========================================================================================
def primary_value(reading):
    """The headline number for ranking: the platform's primary metric if present,
    else the sum of whatever numeric metrics were recorded (0 when none)."""
    metrics = reading.get("metrics") or {}
    key = PRIMARY_METRIC.get(reading["platform"])
    if key in metrics and isinstance(metrics[key], (int, float)):
        return metrics[key]
    return sum(v for v in metrics.values() if isinstance(v, (int, float)))


def summarize(ledger):
    """Rows for the latest snapshot, ranked by primary value, each with its delta
    vs the same post in the previous snapshot (None when first seen). Returns
    {date, prev_date, rows:[{key,hl,platform,title,url,value,delta,metrics}]}."""
    snaps = ledger.get("snapshots", [])
    if not snaps:
        return {"date": None, "prev_date": None, "rows": []}
    latest = snaps[-1]
    prev = snaps[-2] if len(snaps) > 1 else None
    prev_by_id = {_reading_id(r): primary_value(r)
                  for r in (prev["readings"] if prev else [])}
    rows = []
    for r in latest["readings"]:
        value = primary_value(r)
        before = prev_by_id.get(_reading_id(r))
        rows.append({**r, "value": value,
                     "delta": (value - before) if before is not None else None})
    rows.sort(key=lambda r: r["value"], reverse=True)
    return {"date": latest["date"],
            "prev_date": prev["date"] if prev else None, "rows": rows}


def format_summary(summary):
    """Plain-text readout for the operator: ranked posts with deltas, primary metric
    shown per row."""
    if not summary["rows"]:
        return "No readings recorded yet."
    head = "Popularity — %s" % summary["date"]
    if summary["prev_date"]:
        head += " (Δ vs %s)" % summary["prev_date"]
    lines = [head, ""]
    for i, r in enumerate(summary["rows"], 1):
        delta = ""
        if r["delta"] is not None:
            delta = "  (%+d)" % r["delta"] if r["delta"] else "  (=)"
        metric = PRIMARY_METRIC.get(r["platform"], "engagement")
        title = (r.get("title") or r["key"])[:48]
        lines.append("%2d. %5d %-8s %-13s [%s] %s%s"
                     % (i, r["value"], metric, r["platform"], r["hl"], title, delta))
    return "\n".join(lines)


# ========================================================================================
# CLI
# ========================================================================================
def _cmd_worklist(args):
    rows = collect_worklist(args.fr or _configured_folder("fr"),
                            args.en or _configured_folder("en"),
                            platforms=args.platform, hls=args.hl)
    print(json.dumps(rows, indent=2, ensure_ascii=False))


def _cmd_bsky(args):
    print(json.dumps(bsky_metrics(args.url), ensure_ascii=False))


def _cmd_record(args):
    raw = sys.stdin.read() if args.from_ in (None, "-") else open(
        args.from_, encoding="utf-8-sig").read()
    readings = json.loads(raw.lstrip("\N{ZERO WIDTH NO-BREAK SPACE}"))  # tolerate a BOM
    ledger = load_ledger(args.ledger)
    record_snapshot(ledger, args.date, readings)
    save_ledger(ledger, args.ledger)
    print("Recorded %d readings into %s for %s." % (len(readings), args.ledger, args.date))


def _cmd_summary(args):
    print(format_summary(summarize(load_ledger(args.ledger))))


def main(argv=None):
    import argparse
    # Windows consoles default to cp1252; our JSON (accented FR titles) and the summary
    # glyphs (Δ, —) need UTF-8 or print() raises UnicodeEncodeError.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Article popularity tracking.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("worklist", help="print every readable post link as JSON")
    w.add_argument("--fr", help="FR posts folder (default: settings_fr.ini)")
    w.add_argument("--en", help="EN posts folder (default: settings_en.ini)")
    w.add_argument("--platform", action="append",
                   help="only this platform (repeatable), e.g. --platform X/Twitter")
    w.add_argument("--hl", action="append", help="only this language: fr or en (repeatable)")
    w.set_defaults(func=_cmd_worklist)

    b = sub.add_parser("bsky", help="scripted Bluesky counts for one post URL")
    b.add_argument("url")
    b.set_defaults(func=_cmd_bsky)

    r = sub.add_parser("record", help="append a readings JSON array to the ledger")
    r.add_argument("--date", required=True, help="snapshot date YYYY-MM-DD")
    r.add_argument("--from", dest="from_", help="readings JSON file (default: stdin)")
    r.add_argument("--ledger", default=DEFAULT_LEDGER)
    r.set_defaults(func=_cmd_record)

    s = sub.add_parser("summary", help="ranked readout + deltas vs the previous run")
    s.add_argument("--ledger", default=DEFAULT_LEDGER)
    s.set_defaults(func=_cmd_summary)

    args = ap.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
