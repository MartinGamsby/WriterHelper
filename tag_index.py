# Tag suggestions index: scans a posts folder to rank tags for the picker.
#
# Two deterministic signals (no LLM):
#   • popular  — overall frequency of each tag across the folder;
#   • matching — for the article being edited, tags ranked by how often they CO-OCCUR
#                with that article's facets on OTHER posts (conditional frequency given
#                the facets). This is the "from the checked facets" suggestion.
#
# Every raw tag is folded to its controlled-vocabulary label in the target language
# ([[tag-vocabulary]]) before counting, so casing/typo/synonym/leak variants aggregate
# onto one concept and the returned labels are ready to drop straight into the tag
# string. The index is cached per (folder, hl) and rebuilt only when the folder's .md
# signature (file count + newest mtime) changes, so it survives the auto-save churn.
import os
import re
from collections import Counter, defaultdict

import yaml

import tag_vocab

_HEADER_RE = re.compile(r'^\s*---\s*\n(.*?)\n---\s*\n', re.S)

# (folder, hl) -> (signature, index_dict)
_CACHE = {}


def _folder_signature(folder):
    """A cheap fingerprint of the folder's .md files: (count, newest mtime). Changes
    whenever a post is added, removed, or saved, so the cache self-invalidates."""
    count = 0
    newest = 0.0
    try:
        entries = os.listdir(folder)
    except OSError:
        return (0, 0.0)
    for name in entries:
        if not name.endswith(".md"):
            continue
        path = os.path.join(folder, name)
        try:
            newest = max(newest, os.path.getmtime(path))
            count += 1
        except OSError:
            pass
    return (count, newest)


def _read_header(path):
    """Parse just the YAML frontmatter of one post; returns a dict or None. Reads only
    up to the closing `---` so large bodies are never loaded."""
    lines = []
    seen_open = False
    try:
        with open(path, mode="r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip() == "---":
                    if seen_open:
                        break
                    seen_open = True
                    continue
                if not seen_open and line.strip():
                    return None             # content before any frontmatter
                if seen_open:
                    lines.append(line)
    except OSError:
        return None
    raw = "".join(lines).replace("[,Gamsblurb]", "[Gamsblurb]")
    try:
        data = yaml.full_load(raw)
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def _build(folder, hl):
    """Scan `folder`, returning {'freq': Counter(label), 'by_facet': {facet: Counter}}.
    Labels are canonical in `hl`; the house tag is dropped (it is on every post)."""
    freq = Counter()
    by_facet = defaultdict(Counter)
    if not os.path.isdir(folder):
        return {"freq": freq, "by_facet": by_facet}
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".md"):
            continue
        header = _read_header(os.path.join(folder, name))
        if not header:
            continue
        facets = [str(f) for f in (header.get("facets") or [])]
        labels = []
        for raw in (header.get("tags") or []):
            label = tag_vocab.canonical_label(str(raw), hl)
            if label and label != tag_vocab.HOUSE_TAG:
                labels.append(label)
        labels = list(dict.fromkeys(labels))        # de-dup within a post
        for label in labels:
            freq[label] += 1
            for facet in facets:
                by_facet[facet][label] += 1
    return {"freq": freq, "by_facet": by_facet}


def _index(folder, hl):
    sig = _folder_signature(folder)
    cached = _CACHE.get((folder, hl))
    if cached is None or cached[0] != sig:
        cached = (sig, _build(folder, hl))
        _CACHE[(folder, hl)] = cached
    return cached[1]


def popular(folder, hl, exclude=(), limit=24):
    """Most-used tags overall (canonical `hl` labels), excluding `exclude`."""
    exclude = set(exclude)
    idx = _index(folder, hl)
    return [label for label, _ in idx["freq"].most_common()
            if label not in exclude][:limit]


def matching(folder, hl, facets, exclude=(), limit=24):
    """Tags ranked by co-occurrence with `facets` on other posts (conditional
    frequency). Empty when the article has no facets — the caller falls back to
    popular. Ties break by overall frequency then label, so the order is stable."""
    exclude = set(exclude)
    facets = [str(f) for f in (facets or [])]
    if not facets:
        return []
    idx = _index(folder, hl)
    scores = Counter()
    for facet in facets:
        scores.update(idx["by_facet"].get(facet, {}))
    ranked = sorted(
        (label for label in scores if label not in exclude),
        key=lambda label: (-scores[label], -idx["freq"][label], label),
    )
    return ranked[:limit]
