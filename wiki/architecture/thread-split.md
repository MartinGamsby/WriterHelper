# thread_split.py — long article → editable thread

Pure, side-effect-free splitting of one long article into a sequence of social posts
(a "thread"). The publish popup previews + lets the author edit the split; the adapters
just post the resulting segments. No Qt, no I/O. Used by [[publishing]] and the Thread
mode in [[social-publishing]].

## Surface

- `SEPARATOR = "---"` — a line that is **only** dashes marks a split point in the
  editable thread textarea. Authors move/add/remove these lines to control the breaks.
- `split_text(text, max_length, number=True) → [str]` — auto-split into segments that
  each fit `max_length`. When `number`, room is reserved for a trailing ` (i/n)` counter
  so numbered segments still fit — but the returned segments are **not** numbered
  (counters are stamped at publish; the editable preview stays counter-free so the author
  never hand-maintains them). Counter width depends on the count which depends on the
  width, so it iterates to a fixed point (`n` only grows → converges in a pass or two).
- `number_segments(segments) → [str]` — append ` (i/n)`; a lone segment is left as-is.
- `join_for_edit(segments) → str` — render to one editable blob (bodies joined by a
  `---` line). Seeds the popup textarea (`prepare_post`'s `thread_text`).
- `split_on_separator(text) → [str]` — inverse: split the edited blob back on any
  dashes-only line (`^\s*-{3,}\s*$`), trimming and dropping blanks.

## Split strategy (coarsest boundary first)

`_chunk` greedily packs at **paragraph** boundaries (`\n{2,}`, falling back to single
newlines if there are no blank lines); any unit still over the limit is broken by
`_fit_unit` at **sentence** (`[.!?…]` + space) → **word** → hard character cut
(`_hard_wrap`, last resort for an unbreakable token like a giant URL). Every returned
segment is guaranteed ≤ the limit.

## Mirror in JS

`js/publish.js` re-implements `split_on_separator` (`segments()`) and `number_segments`
(`numberedSegments()`) so the live per-segment count AND the preview cards match what
`publish` will send. Keep the two in sync (same `^\s*-{3,}\s*$` rule, same ` (i/n)`
suffix). The preview dock ([[social-publishing]]) renders `numberedSegments` as stacked
cards.

## See also
- [[social-publishing]] — the Thread mode + popup · [[publishing]] — `_publish_thread`
- [[bluesky-adapter]] · [[x-adapter]] — the reply-chaining `post_thread`
