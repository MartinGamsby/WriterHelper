# Link slots

`Link(url, text)` pairs stored in `ArticleModel.links` (order matters — it's the footer
render order). They surface in the meta column, the saved file's footer, and the
[[social-publishing]] idempotence guard.

## Storage

`set_link(text, url)` upserts: replace the URL if a Link with `text` exists, else
append. `get_link(name)` returns the URL or `""`. On load, [[serializers]] populates
`links` by matching `- [name](target)` footer entries. The target is **not** required
to be an `http` URL and **may span multiple lines** — legacy Bluesky slots in the
back-catalog hold the post *text* (multi-line) instead of a URL, and that data must
round-trip rather than be silently dropped on the next auto-save. The parser splits the
footer at each `- [` so a multi-line target stays attached to its own entry; per-entry
the target runs to the entry's final `)`, keeping a trailing `)` inside a URL
(Wikipedia-style `…/Foo_(bar)`) intact.

## Named slots

The meta column exposes these slots, language-conditional (from `LINK_SLOTS` in
`webapi.py`):

| Slot | Visible on | Behaviour |
|---|---|---|
| Medium | FR | text field |
| Typeshare | EN | text field |
| X/Twitter | both | publish button → popup ([[social-publishing]]) |
| LinkedIn | EN | text field ([[linkedin-adapter]] is broken/unused) |
| Facebook | both | publish button → popup ([[facebook-adapter]]) |
| Bluesky | both | publish button → popup |
| YouTube | both | text field; preferred Bluesky link-card source ([[social-publishing]]) |
| YouTube Shorts | both | text field; Bluesky link-card source |
| Source | both | text field |
| "Based on" / "Basé sur" | both | appended dynamically; label = `get_based_on_text()` |

The "Based on" link is auto-seeded by `new_article(copy_current=True)` (the "Make V2"
button), pointing at the previous version's URL.

## Footer rendering

`footer_md()` emits one `- [text](url)\n` line per link with a non-empty URL, into the
`<FOOTER>` slot. Empty-URL Links stay in memory (slot "claimed") but are skipped on
render. In [[astro-format]] the whole `---` + footer block is omitted when there are no
links.

## Why it matters

- The publish guard (`if self.get_link(name): return`) prevents accidental
  double-posting. To re-post, clear the URL field first.
- The footer survives the save/reload round-trip — `change_article` re-extracts the
  same links, including non-URL/multi-line legacy targets, so a re-save never deletes a
  slot it couldn't recognize.
- The "Based on" / "Basé sur" *name* differs per side (`hl`-specific text), so a
  translated copy won't auto-translate that link's name; it's set independently.

## See also
- [[article-model]] · [[social-publishing]] · [[templates]]
