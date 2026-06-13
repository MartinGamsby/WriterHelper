# publishing.py

The two-phase social-post flow + the `PLATFORMS` registry. The design (decision logic,
popup, invariants) is in the concept page [[social-publishing]]; this is the module
reference.

## Surface

- `PLATFORMS` — registry mapping key → `Platform(key, label, link_name, max_length,
  make_poster)`. `make_poster` imports the adapter **lazily** so a missing/broken
  adapter doesn't break import and tests can monkeypatch the registry.

  | key | label | link slot | max_length | adapter |
  |---|---|---|---|---|
  | `bluesky` | Bluesky | `Bluesky` | 300 | `PostBsky(hl)` ([[bluesky-adapter]]) |
  | `x` | X / Twitter | `X/Twitter` | 280 | `PostX(hl)` ([[x-adapter]]) |

- `prepare_post(article, platform_key) → dict` — NO side effects; fills the popup
  (includes `facets_ok`).
- `publish(article, platform_key, mode, message) → {ok, url, error}` — the only method
  with side effects: guards (existing link, mandatory facet), calls
  `poster.post(msg, image_local_url, alt_text)`, stores the URL via `set_link` (re-saves
  the footer), opens it with `webbrowser.open`.
- `image_filename(hl)` → `richTextArea_<hl>1.png` (the load-bearing PNG name).

The adapters (`post.py`, `post_bsky.py`, `post_x.py`) are invoked through here rather
than the old `ArticleModel.post` (which survives only in legacy `model.py`).

## See also
- [[social-publishing]] — the full flow + popup
- [[post-base]] · [[bluesky-adapter]] · [[x-adapter]] · [[link-slots]]
