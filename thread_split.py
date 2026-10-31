# Splitting one long article into a sequence of social posts (a "thread").
# Pure + side-effect-free so the publish popup can preview/edit the split and the
# adapters just post the segments. No Qt, no I/O.
import re

# A line that is ONLY dashes marks a split point in the editable thread textarea.
# Authors move/add/remove these lines to control where the thread breaks.
SEPARATOR = "---"
_SEP_RE = re.compile(r'^\s*-{3,}\s*$', re.MULTILINE)
_SENTENCE_RE = re.compile(r'(?<=[.!?…])\s+')


# ========================================================================================
def _greedy(units, limit, joiner):
    """Pack `units` into the fewest chunks that each stay within `limit`, keeping
    order and re-joining with `joiner`. Units longer than `limit` must already have
    been broken down by the caller."""
    chunks, cur = [], ""
    for u in units:
        if not cur:
            cur = u
        elif len(cur) + len(joiner) + len(u) <= limit:
            cur += joiner + u
        else:
            chunks.append(cur)
            cur = u
    if cur:
        chunks.append(cur)
    return chunks


def _hard_wrap(token, limit):
    """Last resort for an unbreakable token (e.g. a giant URL): cut every `limit`."""
    return [token[i:i + limit] for i in range(0, len(token), limit)]


def _fit_unit(unit, limit):
    """Guarantee a single unit fits, breaking at the coarsest boundary that works:
    sentence → word → hard character cut."""
    if len(unit) <= limit:
        return [unit]
    sentences = _SENTENCE_RE.split(unit)
    if len(sentences) > 1:
        out = []
        for chunk in _greedy(sentences, limit, " "):
            out.extend([chunk] if len(chunk) <= limit else _fit_unit(chunk, limit))
        return out
    words = unit.split(" ")
    if len(words) > 1:
        out = []
        for chunk in _greedy(words, limit, " "):
            out.extend([chunk] if len(chunk) <= limit else _hard_wrap(chunk, limit))
        return out
    return _hard_wrap(unit, limit)


def _chunk(text, limit):
    """Split `text` into readable segments each within `limit`. Prefers paragraph
    boundaries, falling back to single newlines, then sentence/word/char splits."""
    text = text.strip()
    if not text:
        return []
    paras = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
    if len(paras) <= 1:
        paras = [p.strip() for p in text.split('\n') if p.strip()]
    units = []
    for p in paras:
        units.extend(_fit_unit(p, limit))
    return _greedy(units, limit, "\n\n")


# ========================================================================================
def _counter(i, n):
    return " (%d/%d)" % (i, n)


def split_text(text, max_length, number=True):
    """Auto-split `text` into thread segments that each fit `max_length`.

    When `number`, room is reserved for a trailing ` (i/n)` counter so that the
    segments still fit once numbered. The returned segments are NOT yet numbered —
    call `number_segments` to stamp the counters (this keeps the editable preview
    free of counters the author would otherwise have to maintain by hand)."""
    base = _chunk(text, max_length)
    if not number or len(base) <= 1:
        return base
    # The counter width depends on the segment count, which depends on the width.
    # `n` only ever grows, so this converges in a couple of passes.
    n = len(base)
    while True:
        segs = _chunk(text, max_length - len(_counter(1, n)))
        if len(segs) <= n:
            return segs
        n = len(segs)


def number_segments(segments):
    """Append a ` (i/n)` counter to each segment. A lone segment is left as-is."""
    n = len(segments)
    if n <= 1:
        return list(segments)
    return [s + _counter(i + 1, n) for i, s in enumerate(segments)]


def join_for_edit(segments):
    """Render segments into one editable blob: bodies separated by a `---` line."""
    return ("\n%s\n" % SEPARATOR).join(segments)


def split_on_separator(text):
    """Inverse of `join_for_edit`: split the edited blob back into segments on any
    dashes-only line, dropping blank segments."""
    return [s.strip() for s in _SEP_RE.split(text) if s.strip()]
