"""One-shot tag normalizer for the bilingual blog (see [[tag-migration]]).

For each FR/EN twin (matched by translationKey) it:
  1. folds every raw tag onto its controlled-vocabulary label in the file's OWN
     language — fixing casing, typos, synonyms, and cross-language leaks ([[tag-vocabulary]]);
  2. unions the *vocabulary* concepts across the twin so both languages carry the same
     popular/reused tags (one-off non-vocabulary tags stay on their own side);
  3. guarantees the house tag (Gamsblurb) is present, exactly once, and last.

It rewrites ONLY the `tags:` frontmatter line — every other byte of the post is left
untouched. DRY-RUN by default; pass --write to apply, then review `git diff` in the site
repo. Folders default to WriterHelper's configured posts paths (settings_{fr,en}.ini).

    python migrate_tags.py            # report what would change
    python migrate_tags.py --write    # apply
"""
import configparser
import os
import re

import tag_vocab
from tag_index import _read_header   # YAML-header-only reader (shared)

_FM_RE = re.compile(r'^(---[ \t]*\n)(.*?\n)(---[ \t]*\n)', re.S)

# Concepts that are mutually exclusive with the house tag: a Quote (Citation) post is a
# quote, not a Gamsblurb, so it carries NO Gamsblurb. In the clean back-catalog these
# were the ONLY posts ever missing the house tag.
HOUSE_EXCLUSIVE = {"Quote"}

# The "Guide pour" column is identified by the Djosh Sho tag; most entries are fiction
# but some are real-life facts. So the Fiction tag is NEVER pair-unioned across a
# guidepour twin — it stays exactly as authored on each side. (A one-off cleanup removed
# the mistakenly-added Fiction tag from the real-life-fact entries; this rule keeps it
# from creeping back via pairing.) The page + the home star key off the Djosh Sho tag,
# independent of Fiction.
GUIDEPOUR_CONCEPT = "Djosh Sho"
FICTION_CONCEPT = "Fiction"


# ========================================================================================
# Pure planning (no disk) — easy to test
# ========================================================================================
def _canon_list(tags, hl):
    """Canonicalize each raw tag to its `hl` vocabulary label, de-duplicating by concept
    (first spelling wins) and keeping non-vocabulary one-offs as-is."""
    out, seen = [], set()
    for raw in tags:
        label = tag_vocab.canonical_label(str(raw), hl)
        if not label:
            continue
        cid = tag_vocab.concept_id(label)
        key = cid if cid else "raw::" + label.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(label)
    return out


def _rebuild_one(canon_list, union_concepts, hl, include_house):
    """A file's final tag list: its own (canonical) tags, then any twin-only vocabulary
    concepts it still lacks. The house tag is dropped from the body and re-appended last
    ONLY when `include_house` — so a quote post ends with no Gamsblurb, even if a previous
    run wrongly added one."""
    result, seen = [], set()
    for label in canon_list:
        cid = tag_vocab.concept_id(label)
        key = cid if cid else "raw::" + label.casefold()
        if key in seen:
            continue
        seen.add(key)
        if label != tag_vocab.HOUSE_TAG:
            result.append(label)
    for cid in union_concepts:
        if cid in seen:
            continue
        seen.add(cid)
        label = tag_vocab.label(cid, hl)
        if label != tag_vocab.HOUSE_TAG:
            result.append(label)
    if include_house:
        result.append(tag_vocab.HOUSE_TAG)
    return result


def plan_pair(en_tags, fr_tags):
    """Given each twin's raw tag lists, return (new_en, new_fr) normalized + matched. The
    house tag is guaranteed on normal posts but withheld from quote posts (a quote isn't
    a Gamsblurb). For a guidepour post (Djosh Sho) the Fiction tag is NOT pair-unioned —
    it stays as authored per side, so a real-life-fact entry keeps its (absent) Fiction."""
    en_canon = _canon_list(en_tags, "en")
    fr_canon = _canon_list(fr_tags, "fr")
    union, seen = [], set()
    for label in en_canon + fr_canon:
        cid = tag_vocab.concept_id(label)
        if cid and cid not in seen:
            seen.add(cid)
            union.append(cid)
    include_house = not any(cid in HOUSE_EXCLUSIVE for cid in union)
    if GUIDEPOUR_CONCEPT in union:                  # don't propagate Fiction across guidepour twins
        union = [cid for cid in union if cid != FICTION_CONCEPT]
    return (_rebuild_one(en_canon, union, "en", include_house),
            _rebuild_one(fr_canon, union, "fr", include_house))


# ========================================================================================
# File rewriting (only the tags: line)
# ========================================================================================
def replace_tags_line(text, new_tags):
    """Return (new_text, changed) with ONLY the frontmatter `tags:` line set to
    `tags: [a,b,c]`. Inserts the line (after `facets:` if present) when missing. The
    body and every other header line are preserved byte-for-byte."""
    m = _FM_RE.match(text)
    if not m:
        return text, False
    head, body, close = m.group(1), m.group(2), m.group(3)
    new_line = "tags: [%s]" % ",".join(new_tags)
    lines = body.split("\n")
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("tags:"):
            if ln == new_line:
                return text, False
            lines[i] = new_line
            break
    else:
        idx = next((i for i, ln in enumerate(lines)
                    if ln.lstrip().startswith("facets:")), None)
        insert_at = (idx + 1) if idx is not None else max(len(lines) - 1, 0)
        lines.insert(insert_at, new_line)
    new_text = head + "\n".join(lines) + close + text[m.end():]
    return new_text, new_text != text


# ========================================================================================
# Orchestration
# ========================================================================================
def _index_by_key(folder):
    """{translationKey: path} for every .md in `folder`; falls back to the filename stem
    when a post has no translationKey, so nothing is skipped."""
    out = {}
    if not os.path.isdir(folder):
        return out
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(folder, name)
        header = _read_header(path) or {}
        key = str(header.get("translationKey") or name[:-3])
        out.setdefault(key, path)
    return out


def _tags_of(path):
    if not path:
        return []
    header = _read_header(path) or {}
    return [str(t) for t in (header.get("tags") or [])]


def _apply(path, new_tags, write):
    with open(path, mode="r", encoding="utf-8") as fh:
        text = fh.read()
    new_text, changed = replace_tags_line(text, new_tags)
    if changed and write:
        with open(path, mode="w", encoding="utf-8", newline="") as fh:
            fh.write(new_text)
    return changed


def migrate(fr_folder, en_folder, write=False, verbose=True):
    """Normalize + pair every twin under the two folders. Returns a summary dict."""
    en_by_key = _index_by_key(en_folder)
    fr_by_key = _index_by_key(fr_folder)
    keys = sorted(set(en_by_key) | set(fr_by_key))
    changed = scanned = 0

    for key in keys:
        en_path, fr_path = en_by_key.get(key), fr_by_key.get(key)
        en_old, fr_old = _tags_of(en_path), _tags_of(fr_path)
        new_en, new_fr = plan_pair(en_old, fr_old)
        for path, old, new in ((en_path, en_old, new_en), (fr_path, fr_old, new_fr)):
            if not path:
                continue
            scanned += 1
            if _apply(path, new, write):
                changed += 1
                if verbose:
                    print("  %s\n    - %s\n    + %s"
                          % (os.path.basename(path), ",".join(old), ",".join(new)))

    if verbose:
        mode = "WROTE" if write else "DRY-RUN (no files changed; pass --write to apply)"
        print("\n%s — %d of %d files would change." % (mode, changed, scanned))
    return {"scanned": scanned, "changed": changed, "write": write}


def _configured_folder(hl, config_dir="."):
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(config_dir, "settings_%s.ini" % hl))
    return cfg["Paths"]["Posts"]


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Normalize + pair blog tags.")
    ap.add_argument("--fr", help="FR posts folder (default: settings_fr.ini)")
    ap.add_argument("--en", help="EN posts folder (default: settings_en.ini)")
    ap.add_argument("--write", action="store_true", help="apply changes (default: dry-run)")
    args = ap.parse_args()
    migrate(args.fr or _configured_folder("fr"),
            args.en or _configured_folder("en"),
            write=args.write)
