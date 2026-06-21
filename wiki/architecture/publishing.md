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
  | `facebook` | Facebook | `Facebook` | 63206 | `PostFB(hl)` ([[facebook-adapter]]) — text/image only, no threads |
  | `instagram` | Instagram | `Instagram` | 2200 | `PostIG(hl)` ([[instagram-adapter]]) — image-only, two-step (stage → publish) |
  | `linkedin` | LinkedIn | `LinkedIn` | 3000 | `PostBridge(hl,"linkedin")` ([[post-bridge-adapter]]) — text/image |
  | `threads` | Threads | `Threads` | 500 | `PostBridge(hl,"threads")` ([[post-bridge-adapter]]) — text/image |
  | `pinterest` | Pinterest | `Pinterest` | 500 | `PostBridge(hl,"pinterest")` ([[post-bridge-adapter]]) — image required |
  | `tiktok` | TikTok | `TikTok` | 2200 | `PostBridge(hl,"tiktok")` ([[post-bridge-adapter]]) — video-only, gated |

  Each `Platform` also carries `supports_thread` (False for Facebook, Instagram, and the
  post-bridge platforms — none override `post_thread`; `prepare_post` reads it to suggest
  **Image** instead of **Thread** for a too-long post) and `media` (`"any"`/`"image"`/
  `"video"` — the required attachment). `prepare_post` exposes `media`; the popup offers
  only image mode for `"image"` and gates `"video"` entirely, and `publish()` re-checks
  both ([[social-publishing]] "Media requirements").

- `stage_instagram_image(article) → {ok, public_url, log, error}` — Instagram **step 1**:
  resolves the grabbed JPEG + the site repo ([[martingamsby-site]] via
  `localize.find_repo_root`), then delegates to `site_push.stage_and_push_image` to copy
  it into `public/assets/ig/<slug>.<hl>.jpg`, git-push it, and return the **public raw
  URL**. Called by the `webapi.publish_instagram_image` bridge method; the popup hands the
  URL back to `publish(...)`. `prepare_post` also exposes `ig_image_pushed` /
  `ig_public_url` (read-only `site_push.image_status`: dest exists, byte-identical to the
  grabbed card, committed + pushed) so a reopened popup skips step 1, plus
  `ig_repo_image_data_url` (the committed image as a data URL) so the popup shows what's
  actually in the repo. See [[instagram-adapter]].
- `prepare_post(article, platform_key) → dict` — NO side effects; fills the popup
  (includes `facets_ok`, the thread seed `thread_text`/`thread_count`/`separator`
  ([[thread-split]]), and `embed_url` — the Bluesky link-card candidate, `""` for other
  platforms since they auto-unfurl).
- `embed_candidate(article, message="") → url` — the URL a Bluesky link-preview card
  would point at: a `YouTube`/`YouTube Shorts` [[link-slots]] wins (deliberate, and
  rendered as a video card), else the first http(s) URL in `message` (trailing
  punctuation trimmed). `""` when neither exists.
- `publish(article, platform_key, mode, message, options=None) → {ok, url, error}` — the
  only method with side effects: guards (existing link, mandatory facet), computes the
  optional `embed_url` (`opts["embed"]` true **and** platform is `bluesky`), then by
  `mode` posts via `poster.post(..., embed_url=)` (text; image mode resolves its
  attachment via `_resolve_image(opts["image"]`, default `"grabbed"`) and omits the
  embed — the image owns that slot) or delegates to `_publish_thread`; stores the URL via `set_link`
  (re-saves the footer), opens it with `webbrowser.open`. **Instagram** is intercepted
  right after the guards → `_publish_instagram` (image-only, no text/thread/embed).
- `_publish_instagram(article, p, caption, opts)` — posts the already-public image
  (`opts["image_url"]` from `stage_instagram_image`) + `caption` via `PostIG.post(...,
  image_url=)`; requires the URL (else "push the image first"), rejects an over-2200
  caption, stores the permalink in the `Instagram` slot. See [[instagram-adapter]].
- `_publish_thread(article, p, message, opts, embed_url=None)` — splits `message` on `---`
  ([[thread-split]]), optionally numbers, rejects any over-limit segment, resolves the
  image via `_resolve_image`, calls `poster.post_thread(..., embed_url=)`; stores `urls[0]`
  as the slot guard, returns `{...,urls}`. `opts = {"number": bool, "image":
  "none"|"grabbed"|"article", "embed": bool}`.
- `_resolve_image(article, source)` → `(local_path, error)`. `"grabbed"` = the captured
  text-card PNG (`image_filename`); `"article"` = the post's own header image as a local
  file (`rendering.excerpt_image_file`, self-hosted on save). Grabbed alt text = full
  plain text; article alt text = the title. Used by **both** thread mode and image mode.
- `capture_filename(article, page)` → `richTextArea_<slug>_<hl><page>.jpg` — the single
  source of truth for the capture name (used by both `webapi.save_capture` and here).
  Slug-named so the capture is tied to its article (the "right article" guarantee);
  JPEG so it doubles as the IG asset ([[instagram-adapter]]).
- `image_filename(article)` → `capture_filename(article, 1)`, the page-1 file image mode
  attaches / IG would commit.
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
