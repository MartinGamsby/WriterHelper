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

## post_thread() — the reply chain

`post_thread(messages, image_local_url, alt_text) → [url]` logs in once, then posts each
message in order. Every reply carries `models.AppBskyFeedPost.ReplyRef(root=<first>,
parent=<previous>)`; the strong ref for each post comes from `models.create_strong_ref(resp)`
(uri+cid). The image (if any) attaches to the **first** post only. Returns one web URL per
post. Used by [[publishing]] `_publish_thread`.

## See also
- [[post-base]] · [[x-adapter]] · [[social-publishing]]
