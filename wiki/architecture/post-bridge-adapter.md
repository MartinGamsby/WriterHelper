# post-bridge adapter (`post_bridge.py`)

`PostBridge(hl, platform)` posts through **post-bridge.com** — a paid aggregator whose
single API key reaches LinkedIn, Threads, Pinterest, TikTok (and more) without a
per-platform developer app or token. It inherits [[post-base]], so [[publishing]] drives
it exactly like the native [[bluesky-adapter]] / [[x-adapter]] / [[facebook-adapter]].
Currently wired for **LinkedIn, Threads, Pinterest, TikTok** ([[social-publishing]]
`PLATFORMS`).

## Why it exists

The native adapters each need their own developer app, OAuth, and token upkeep — the
LinkedIn one was never finished ([[linkedin-adapter]], BROKEN). post-bridge trades that
setup tax for one key + a yearly fee, and — unlike the Meta Instagram path — it accepts a
**local** image upload, so attaching the grabbed card needs **no public-URL git staging**
([[instagram-adapter]] contrast).

## Config — one file, every platform, both languages

`settings_postbridge.ini` (hl-independent, git-ignored — [[secrets]]):
- `[Access] ApiKey` — the `pb_live_…` key (the secret).
- `[Accounts]` — *optional* pins mapping an account id per platform/language. Keys tried
  in order: `<platform>_<hl>` then `<platform>` (comma-separated ids allowed). Absent ⇒
  auto-resolve.

## Account resolution (the bilingual safety valve)

`_resolve_account_ids()` decides which post-bridge **social_account id(s)** a post
targets:
1. A pin in `[Accounts]` wins (language key first, then bare platform).
2. Else auto-resolve from `GET /v1/social-accounts` by matching `platform`:
   - **exactly one** match → use it (the zero-config single-account case);
   - **several** matches, no pin → **refuse** and list them, so a FR post can't silently
     land on an EN account. The operator pins the right id per language.
   - **none** → refuse with "connect one in the dashboard".

## post() flow

`post(msg, image_local_url, alt_text, embed_url=None) → url` ([[post-base]] contract;
`embed_url` ignored — these platforms unfurl caption links themselves):
1. resolve account id(s).
2. if an image is attached → `_upload_image`: `POST /v1/media/create-upload-url`
   `{mime_type, size_bytes, name}` → `{media_id, upload_url}`, then **PUT the bytes** to
   the signed `upload_url` (JPEG/PNG only; other types rejected). Local upload — no
   staging.
3. `POST /v1/posts` `{caption, social_accounts:[id…], media:[media_id]?}` (no
   `scheduled_at` ⇒ instant) → `{id}`.
4. `_resolve_post_url`: poll `GET /v1/post-results?post_id=` until this account's
   `platform_data.url` appears (it's minted **asynchronously**). A `success:false` row is
   raised with its `error`; if no URL after the poll budget, raise the **manual-link**
   instruction (paste the URL by hand to avoid a blind re-post — same convention as
   [[instagram-adapter]]'s permalink fallback). That URL becomes the [[link-slots]] guard.

API failures are wrapped in `PostBridgeError` with an operator-facing message;
[[publishing]]'s `try/except` surfaces it in the popup.

## No threads

`post_thread` is **not** overridden — post-bridge has no native reply chain, so the base
`NotImplementedError` stands and these platforms are marked `supports_thread=False` in
`PLATFORMS`. `prepare_post` therefore suggests **Image** (not Thread) for a too-long post
([[social-publishing]]). Text + Image are the supported modes.

## Endpoints (confirmed from the official `post-bridge-api` npm client, v0.1.1)

Base `https://api.post-bridge.com`, `Authorization: Bearer <key>`:
`GET /v1/social-accounts` · `POST /v1/media/create-upload-url` (+ PUT signed URL) ·
`POST /v1/posts` · `GET /v1/post-results?post_id=`.

## Media requirements per platform

The four wired platforms differ in what they *require* (`Platform.media`, see
[[social-publishing]]): **LinkedIn / Threads** = `"any"` (text or image); **Pinterest** =
`"image"` (the popup offers only Title + image); **TikTok** = `"video"` — and since
WriterHelper authors no video, its popup is a **gate** (post by hand, paste the URL). If
WriterHelper ever produces a video asset, TikTok flips to a real composer by changing its
`media` and giving the adapter a video to upload (post-bridge's upload enum already allows
`video/mp4`, `video/quicktime`) — this is the [[video-posts]] roadmap (TikTok then YouTube
Shorts).

## Extending

- **More platforms**: add a `Platform(..., _make_pb("<name>"), supports_thread=False)`
  row + a `LINK_SLOTS` entry. The adapter is platform-agnostic.
- **Replace X** (it's pay-per-use): point the `x` registry row at `_make_pb("x")` — but
  that loses the native thread chain + link-card tailoring, so it's a deliberate trade.
- **Scheduling**: post-bridge accepts `scheduled_at` on `POST /v1/posts`; instant posting
  just omits it.

## See also
- [[publishing]] · [[social-publishing]] · [[post-base]] · [[link-slots]] · [[secrets]]
- [[linkedin-adapter]] — the broken native LinkedIn attempt this supersedes for posting
- [[instagram-adapter]] — the public-URL staging this avoids
