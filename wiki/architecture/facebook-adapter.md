# Facebook adapter (`post_fb.PostFB`)

Posts to a Facebook **Page** via the Graph API. Inherits [[post-base]] and is wired into
the UI: the Facebook link slot is a Publish button on **both** languages
([[link-slots]]), routing through [[publishing]]'s `PLATFORMS["facebook"]`.

## Config

`settings_fb_<hl>.ini` — `[Access]` with `PageId` (the Page's numeric id) and `Token` (a
**long-lived Page access token**). See [[secrets]].

The token needs the `pages_manage_posts` permission. A short-lived user token won't
work — you need the **non-expiring Page token**. **This token/permission step is the
usual reason "Facebook didn't work", not the code.**

### Getting the non-expiring Page token

You manage the Page and own the app, so this works in the app's **Development mode** —
no full App Review needed (review is only for posting to *other people's* Pages).

1. **App**: at [developers.facebook.com](https://developers.facebook.com) create an app
   (type *Business*) if you don't have one. Note its **App ID** + **App Secret**
   (Settings → Basic).
2. **Short-lived user token**: open **Tools → Graph API Explorer**, pick your app, and
   add permissions `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`
   (+ `public_profile`). Click **Generate Access Token** and approve for your Page.
3. **Exchange for a long-lived user token** (≈60 days):
   `GET https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=<APP_ID>&client_secret=<APP_SECRET>&fb_exchange_token=<SHORT_TOKEN>`
4. **Read the Page token** (this one effectively **never expires**):
   `GET https://graph.facebook.com/v21.0/me/accounts?access_token=<LONG_USER_TOKEN>`
   The response lists each Page with its numeric **`id`** (→ `PageId`) and a per-Page
   **`access_token`** (→ `Token`).
5. Put `PageId` + `Token` into `settings_fb_<hl>.ini`. (Same Page for both langs? Put the
   same values in both files.)

Meta's reference: <https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived/>.
Sanity-check a token in **Tools → Access Token Debugger** (look for `pages_manage_posts`
under scopes and "Expires: Never").

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
