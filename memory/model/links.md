# Links

A cross-cutting concept: `Link(url, text)` pairs are stored in `ArticleModel.links` and surfaced in the UI, the saved file's footer, and the social-post idempotence guard.

## Storage

`ArticleModel.links: list[Link]` — order matters (it's the order the footer renders in). `set_link(text, url)` upserts: if a Link with `text` exists, replace its `url`; else append. `get_link(name)` returns the URL or `""`.

`change_article` populates `links` from the file's footer by regex-matching `[name](url)` pairs.

## Named slots

The UI in `ArticleMeta.qml` exposes these slots, language-conditional:

| Slot | Visible on | Notes |
|---|---|---|
| Medium | FR | text field only |
| Typeshare | EN | text field only |
| X/Twitter | both | label clicks → `post_x()` |
| LinkedIn | EN | text field only |
| Facebook | FR | text field only |
| Bluesky | both | label clicks → `post_bluesky()` |
| YouTube | both | text field only |
| YouTube Shorts | both | text field only |
| Source | both | text field only |
| "Based on" / "Basé sur" | both | label text is `get_based_on_text()` — `"Based on"` if EN else `"Basé sur"` |

The "Based on" link is auto-seeded by `new_article(copy_current=True)` (the "Make V2" button), pointing back to the previous version's URL.

## Footer rendering

`footer_md()` produces one `- [text](url)\n` line per link with a non-empty URL. Inserted into `<FOOTER>` placeholder of `templates/post.md`. Empty-URL Links are kept in memory (since the slot has been "claimed") but skipped on render.

## Why this matters

- The post-routing guard (`if self.get_link(name): return`) prevents accidental double-posting. To intentionally re-post, clear the URL TextField in the UI first.
- The footer is what survives a save/reload round-trip — `change_article` re-extracts the same links via regex.
- The "Based on" / "Basé sur" name is also looked up by `get_link_based_on()`, which uses the `hl`-specific text. So the *name* of the link slot differs between FR and EN. A copied article translated FR→EN won't auto-translate this link's *name*; it's set independently per side.

## See also
- [article-model.md](article-model.md)
- [post-routing.md](post-routing.md)
- [../ui/qml-tree.md](../ui/qml-tree.md)
- [../templates/summary.md](../templates/summary.md)
