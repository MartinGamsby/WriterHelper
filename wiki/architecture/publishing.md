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
  (includes `facets_ok` and the thread seed `thread_text`/`thread_count`/`separator`,
  [[thread-split]]).
- `publish(article, platform_key, mode, message, options=None) → {ok, url, error}` — the
  only method with side effects: guards (existing link, mandatory facet), then by `mode`
  posts via `poster.post(...)` (text/image) or delegates to `_publish_thread`; stores the
  URL via `set_link` (re-saves the footer), opens it with `webbrowser.open`.
- `_publish_thread(article, p, message, opts)` — splits `message` on `---`
  ([[thread-split]]), optionally numbers, rejects any over-limit segment, resolves the
  image via `_resolve_image`, calls `poster.post_thread(...)`; stores `urls[0]` as the
  slot guard, returns `{...,urls}`. `opts = {"number": bool, "image":
  "none"|"grabbed"|"article"}`.
- `_resolve_image(article, source)` → `(local_path, error)`. `"grabbed"` = the captured
  text-card PNG (`image_filename`); `"article"` = the post's own header image as a local
  file (`rendering.excerpt_image_file`, self-hosted on save). Grabbed alt text = full
  plain text; article alt text = the title.
- `image_filename(article)` → `richTextArea_<hl>1.png` (the load-bearing PNG name).
- `_post_error(p, exc)` / `_log_post_exc(p, exc)` — the adapter call in `publish`/
  `_publish_thread` is wrapped in `try/except`: an auth/network failure becomes a normal
  `{ok: False, error}` (via `_post_error`, which special-cases X's `client-not-enrolled`
  403) instead of propagating. `_log_post_exc` still prints the full stack + tweepy
  `api_codes`/HTTP body to stderr. This pairs with `js/publish.js` `send()` wrapping the
  bridge call in try/catch, so a posting failure shows in the popup rather than leaving it
  stuck on "Publishing…". See [[x-adapter]] for the pay-per-use 403.

The adapters (`post.py`, `post_bsky.py`, `post_x.py`) are invoked through here rather
than the old `ArticleModel.post` (which survives only in legacy `model.py`).

## See also
- [[social-publishing]] — the full flow + popup
- [[thread-split]] — the pure splitter behind Thread mode
- [[post-base]] · [[bluesky-adapter]] · [[x-adapter]] · [[link-slots]]
