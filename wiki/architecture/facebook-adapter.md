# Facebook adapter (`post_fb.PostFB`)

Posts to a Facebook **Page** via the Graph API. Inherits [[post-base]] and is wired into
the UI: the Facebook link slot is a Publish button on **both** languages
([[link-slots]]), routing through [[publishing]]'s `PLATFORMS["facebook"]`.

## Config

`fb_settings_<hl>.ini` — `[Access]` with `PageId` (the Page's numeric id) and `Token` (a
**long-lived Page access token**). Note the filename prefix (`fb_settings_` vs the newer
`settings_<platform>_` pattern) is kept for backward-compat with the operator's existing
files. See [[secrets]].

The token needs the `pages_manage_posts` permission (and the app must clear Meta's app
review for it). A short-lived user token won't work — exchange it for a long-lived Page
token in the Graph API Explorer / token tool first. **This token/permission step is the
usual reason "Facebook didn't work", not the code.**

## API

Graph API (version pinned in the module constant `GRAPH_API_VERSION`, currently
`v21.0` — bump when Meta retires the version):

- `post(msg, image_local_url, alt_text) → url`:
  - **with image** → `POST /{page_id}/photos`, the local file uploaded as the `source`
    multipart part, `alt_text` sent as `alt_text_custom`. Response carries `post_id`
    (the feed-post id) → that's used for the URL.
  - **without image** → `POST /{page_id}/feed`. Response `{"id": "<page>_<post>"}`.
  - returns `https://www.facebook.com/<post_id|id>`; **raises `RuntimeError`** on a Graph
    `error` payload or a missing id, so [[publishing]]'s try/except surfaces it in the
    popup (`_post_error`/`_log_post_exc`).

`get_handle()` is overridden to return the Page id so the [[post-base]] `__init__` log
line works (FB has no handle field).

## No threads

`PostFB` does **not** override `post_thread`, so Thread mode raises
`NotImplementedError` (caught → popup error). It's a non-issue in practice: Facebook's
~63k-char limit (`max_length=63206`) means a post always `fits`, so `suggested_mode` is
always `text`. Text and image modes are the supported paths.

## Fixed bug

The pre-rewrite class assigned `self.config['Access']` **twice** in `__init__`, so the
second assignment (`PageId`) wiped `Token` and `get_token()` raised `KeyError`. Now a
single `access={'PageId':…, 'Token':…}` dict carries both. Regression test:
`tests/test_post_fb.py::test_get_token_and_page_id_both_survive_init`.

## Tests

`tests/test_post_fb.py` mocks `requests.post` to assert the feed/photos edge, the
`source` upload, `alt_text_custom`, the built URL (uses `post_id` for photos), and that a
Graph `error` becomes a `RuntimeError`. Platform-wiring cases live in
`tests/test_publishing.py` (`fake_fb` fixture).

## See also
- [[post-base]] · [[publishing]] · [[social-publishing]] · [[link-slots]] · [[secrets]]
