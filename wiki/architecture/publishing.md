# publishing.py

The two-phase social-post flow + the `PLATFORMS` registry. The design (decision logic,
popup, invariants) is in the concept page [[social-publishing]]; this is the module
reference.

## Module split

- `platforms.py` — `Platform` + the `PLATFORMS` registry + `is_hidden`. `publishing`
  re-exports `PLATFORMS`/`Platform` (tests monkeypatch `publishing.PLATFORMS`, the same
  dict).
- `publishing.py` — `prepare_post` / `publish` / `_plan` / capture naming / errors.
- `instagram_flow.py` — Instagram over the Graph API (stage → publish); used only when
  Instagram's transport is `api`.
- `browser_jobs.py` + `publish_config.py` — the browser hook ([[browser-hook]]).

## Surface

- `PLATFORMS` — key → `Platform(key, label, link_name, max_length, make_poster,
  supports_thread=True, media="any", browser_url="", default_transport=None)`.
  `make_poster` (or None = browser-only) imports the adapter **lazily**. `transport`
  (property) = the `settings_publish.ini [Transport]` pin if that route exists, else the
  default (`api` when an adapter exists, unless overridden); `via` = `"browser"`/`""`.

  | key | label | slot | max | media | thread | transport (default · alt) |
  |---|---|---|---|---|---|---|
  | `bluesky` | Bluesky | `Bluesky` | 300 | any | ✓ | api `PostBsky` ([[bluesky-adapter]]) |
  | `x` | X / Twitter | `X/Twitter` | 280 | any | ✓ | browser · api `PostX` ([[x-adapter]]) |
  | `facebook` | Facebook | `Facebook` | 63206 | any | — | browser · api `PostFB` ([[facebook-adapter]]) |
  | `instagram` | Instagram | `Instagram` | 2200 | image | — | browser · api `PostIG` ([[instagram-adapter]]) |
  | `linkedin` | LinkedIn | `LinkedIn` | 3000 | any | — | browser |
  | `threads` | Threads | `Threads` | 500 | any | ✓ | browser |
  | `pinterest` | Pinterest | `Pinterest` | 500 | image | — | browser |
  | `tiktok` | TikTok | `TikTok` | 2200 | image (photo post) | — | browser |
  | `medium` | Medium | `Medium` | 100000 | any | — | browser |

- `stage_instagram_image(article) → {ok, public_url, log, error}` — Instagram-over-API
  **step 1** (delegates to `instagram_flow.stage_image`): resolves the grabbed JPEG + the
  site repo ([[martingamsby-site]] via
  `localize.find_repo_root`), then delegates to `site_push.stage_and_push_image` to copy
  it into `public/assets/ig/<slug>.<hl>.jpg`, git-push it, and return the **public raw
  URL**. Called by the `webapi.publish_instagram_image` bridge method; the popup hands the
  URL back to `publish(...)`. `prepare_post` (API transport only, via
  `instagram_flow.prepare_extras`) also exposes `ig_image_pushed` /
  `ig_public_url` (read-only `site_push.image_status`: dest exists, byte-identical to the
  grabbed card, committed + pushed) so a reopened popup skips step 1, plus
  `ig_repo_image_data_url` (the committed image as a data URL) so the popup shows what's
  actually in the repo. See [[instagram-adapter]].
- `prepare_post(article, platform_key) → dict` — NO side effects; fills the popup
  (includes `transport`/`via`/`compose_url`, `pending_job` + `hook_command` (browser
  only, [[browser-hook]]), `facets_ok`, the thread seed `thread_text`/`thread_count`/`separator`
  ([[thread-split]]), and `embed_url` — the Bluesky link-card candidate, `""` for other
  platforms since they auto-unfurl).
- `embed_candidate(article, message="") → url` — the URL a Bluesky link-preview card
  would point at: a `YouTube`/`YouTube Shorts` [[link-slots]] wins (deliberate, and
  rendered as a video card), else the first http(s) URL in `message` (trailing
  punctuation trimmed). `""` when neither exists.
- `publish(article, platform_key, mode, message, options=None)` — the only function with
  side effects: guards (facet, existing link, pending browser job, video, IG-over-API
  intercept → `instagram_flow.publish`, image-required), then `_plan` builds
  `(posts, image, alt_text)`; **browser** → `browser_jobs.create` + `run_hook` →
  `{ok, queued, job, hook}`; **api** → `post_thread`/`post` (Bluesky `embed_url` only in
  text/thread) → `set_link(urls[0])` + `webbrowser.open` → `{ok, url[, urls]}`. Full
  step list: [[social-publishing]].
- `_plan(article, p, mode, message, opts)` → `(posts, image, alt_text, error)` — the
  transport-agnostic validation shared by both routes (thread split/number/limits,
  blank text, char limit, image resolution, alt text).
- `_resolve_image(article, source)` → `(local_path, error)`. `"grabbed"` = the captured
  text-card JPEG (`image_filename`); `"article"` = the post's own header image as a local
  file (`rendering.excerpt_image_file`, self-hosted on save). Grabbed alt text = full
  plain text; article alt text = the title. Used by **both** thread mode and image mode.
- `capture_filename(article, page)` → `richTextArea_<slug>_<hl><page>.jpg` — the single
  source of truth for the capture name (used by both `webapi.save_capture` and here).
  Slug-named so the capture is tied to its article (the "right article" guarantee);
  JPEG so it doubles as the IG asset ([[instagram-adapter]]).
- `image_filename(article)` → `capture_filename(article, 1)`, the page-1 file image mode
  attaches / IG would commit.
- `_post_error(p, exc)` / `_log_post_exc(p, exc)` — the adapter call in `publish`/
  `instagram_flow.publish` is wrapped in `try/except` (`_failure`): an auth/network failure becomes a normal
  `{ok: False, error}` (via `_post_error`, which special-cases X's `client-not-enrolled`
  403) instead of propagating. `_log_post_exc` still prints the full stack + tweepy
  `api_codes`/HTTP body to stderr. This pairs with `js/publish.js` `send()` wrapping the
  bridge call in try/catch, so a posting failure shows in the popup rather than leaving it
  stuck on "Publishing…". See [[x-adapter]] for the pay-per-use 403.

The adapters (`post.py`, `post_bsky.py`, `post_x.py`, `post_fb.py`, `post_ig.py`) are
invoked through here rather than the old `ArticleModel.post` (which survives only in
legacy `model.py`).

## See also
- [[social-publishing]] — the full flow + popup
- [[browser-hook]] — the Claude in Chrome route
- [[thread-split]] — the pure splitter behind Thread mode
- [[post-base]] · [[bluesky-adapter]] · [[x-adapter]] · [[link-slots]]
