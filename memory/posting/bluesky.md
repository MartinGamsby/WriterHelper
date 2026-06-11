# BlueSky — `post_bsky.PostBsky`

Inherits [Post](post-base.md). Uses the [`atproto`](https://pypi.org/project/atproto/) Python SDK.

## Config

`settings_bsky_<hl>.ini`:

```ini
[Access]
handle = your-handle.bsky.social
apppassword = xxxx-xxxx-xxxx-xxxx
```

`apppassword` is a BlueSky **app password** (settings → privacy & security → app passwords), not the account password.

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

- Login each call (no session reuse).
- Text-only path: `send_post`.
- Image path: reads bytes, calls `send_image` with `image_alt`.
- `langs=[self.hl]` advertises the post language.
- Returns the rendered web URL (constructed from handle + post id), not the raw `at://` URI.

## Limits

- 300 characters (set as `max_length` in `ArticleModel.post_bluesky`).
- One image only (more is possible via embed objects, not used here).

## See also
- [post-base.md](post-base.md)
- [summary.md](summary.md)
- [../model/post-routing.md](../model/post-routing.md)
