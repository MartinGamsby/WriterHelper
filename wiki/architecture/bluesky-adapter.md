# Bluesky adapter (`post_bsky.PostBsky`)

Inherits [[post-base]]. Uses the `atproto` Python SDK. Limit 300 chars, one image.

## Config

`settings_bsky_<hl>.ini` — `[Access]` with `handle` (`your-handle.bsky.social`) and
`apppassword` (a Bluesky **app password**, not the account password). Git-ignored, see
[[secrets]].

## post() implementation

```python
def post(self, msg, image_local_url, alt_text):
    client = Client()
    client.login(self.get_handle(), self.get_app_password())
    if image_local_url and os.path.isfile(image_local_url):
        with open(image_local_url, 'rb') as f:
            post = client.send_image(text=msg, image=f.read(),
                                     image_alt=alt_text, langs=[self.hl])
    else:
        post = client.send_post(msg, langs=[self.hl])
    uri = post.uri              # at://did:plc:.../app.bsky.feed.post/<id>
    id = uri[uri.rfind("/")+1:]
    return f"https://bsky.app/profile/{self.get_handle()}/post/{id}"
```

- Logs in each call (no session reuse). Text path = `send_post`; image path reads bytes,
  `send_image` with `image_alt`. `langs=[self.hl]` advertises the post language. Both
  paths go through `_send(...)`, which also takes a `reply_to`; URL building is factored
  into `_post_url(uri)`.
- Returns the rendered web URL (handle + post id), not the raw `at://` URI.

## Clickable links (rich-text facets)

Bluesky renders a bare URL as **plain, un-clickable text** unless the post record
carries link *facets*. `_send` runs the message through module-level `build_rich_text(msg)`
first, so every post (single **and** thread) gets clickable links for free:

- `build_rich_text(msg)` scans for `https?://…` URLs (`_URL_RE`). **No URL → returns the
  plain string unchanged** (non-link posts behave exactly as before). One or more URLs →
  returns an `atproto.client_utils.TextBuilder` interleaving `.text(...)` runs and
  `.link(url, url)` facets. Both `send_post` and `send_image` accept `str | TextBuilder`.
- `_trim_url` strips trailing sentence punctuation (`.,;:!?'"`) the regex swallowed, and
  drops a trailing `)]}` **only when unbalanced** — so `…/Foo_(bar)` Wikipedia links keep
  their inner parens.
- `TextBuilder` computes facet ranges as **UTF-8 byte offsets**, so multi-byte text
  before a URL (FR accents, arrows) keeps the link aligned. Covered by `test_post_bsky.py`.
- This is the only adapter with link facets: X auto-links URLs server-side, and Facebook
  Graph posts do too — no equivalent needed there.

## Link-preview card (external embed)

Optional, opt-in via a popup checkbox ([[social-publishing]]). When `post`/`post_thread`
receive an `embed_url`, `_send` builds an `app.bsky.embed.external` card and passes it as
`send_post(..., embed=...)`. Module-level `fetch_external_card(client, url)` does the work:

- GETs `url` (browser-ish UA), parses OpenGraph `og:title`/`og:description`/`og:image`
  with BeautifulSoup, uploads the thumbnail via `client.upload_blob(bytes).blob` (a real
  `BlobRef` — the `External` model rejects anything else), returns
  `models.AppBskyEmbedExternal.Main`.
- **YouTube** links (`youtube_id` matches watch/shorts/youtu.be/embed/live) skip image
  scraping and use `https://img.youtube.com/vi/<id>/hqdefault.jpg` directly — reliable,
  and Bluesky renders the card as a playable video.
- **Fail-soft**: any fetch/parse/upload error → returns None (logged to stderr); a missing
  card must never block the post. A failed thumb still yields a text-only card.
- A post's embed slot holds **either** an image **or** an external card. `_send` honours
  `embed_url` only when no image is attached; in a thread the card rides the **first**
  post and only if that post has no image. Covered by `test_post_bsky.py`.

The candidate URL is chosen upstream in `publishing.embed_candidate` ([[publishing]]):
a YouTube/YouTube Shorts [[link-slots]] wins, else the first URL in the message.

## post_thread() — the reply chain

`post_thread(messages, image_local_url, alt_text) → [url]` logs in once, then posts each
message in order. Every reply carries `models.AppBskyFeedPost.ReplyRef(root=<first>,
parent=<previous>)`; the strong ref for each post comes from `models.create_strong_ref(resp)`
(uri+cid). The image (if any) attaches to the **first** post only. Returns one web URL per
post. Used by [[publishing]] `_publish_thread`.

## See also
- [[post-base]] · [[x-adapter]] · [[social-publishing]]
