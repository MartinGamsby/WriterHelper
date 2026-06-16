# Link slots

`Link(url, text)` pairs stored in `ArticleModel.links` (order matters — it's the footer
render order). They surface in the meta column, the saved file's footer, and the
[[social-publishing]] idempotence guard.

## Storage

`set_link(text, url)` upserts: replace the URL if a Link with `text` exists, else
append. `get_link(name)` returns the URL or `""`. On load, [[serializers]] populates
`links` by regex-matching `[name](url)` pairs in the file footer.

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
| YouTube | both | text field |
| YouTube Shorts | both | text field |
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
  same links by regex.
- The "Based on" / "Basé sur" *name* differs per side (`hl`-specific text), so a
  translated copy won't auto-translate that link's name; it's set independently.

## See also
- [[article-model]] · [[social-publishing]] · [[templates]]
