# Facebook adapter (`post_fb.PostFB`)

⚠️ Does **NOT** inherit [[post-base]] (it predates the base class) and is **NOT** wired
into the UI. FB posting is currently manual (the legacy checklist, [[legacy-qt-ui]]).

## Config

`fb_settings_<hl>.ini` — `[Access]` with `token` (page access token) and `pageid`. Note
the filename prefix (`fb_settings_` vs the newer `settings_<platform>_` pattern). See
[[secrets]].

## API

Facebook Graph API v18.0 via `requests.post`:

```python
def post_to_fb_page(self, msg, image_url):
    if image_url:
        url = f'https://graph.facebook.com/v18.0/{self.get_page_id()}/photos'
        payload = {'message': msg, 'access_token': self.get_token(), 'url': image_url}
    else:
        url = f'https://graph.facebook.com/v18.0/{self.get_page_id()}/feed'
        payload = {'message': msg, 'access_token': self.get_token()}
    r = requests.post(url, data=payload)
    return 'id' in r.json()    # bool, not a URL
```

Differences vs the modern adapters: method is `post_to_fb_page` not `post`; returns
`bool` not a URL (so it can't feed `set_link` directly); takes a remote `image_url`, not
a local path.

## To integrate later

Either subclass `Post` and rename `post_to_fb_page` → `post` returning a constructed
URL, or keep the old shape and add a separate routing path. See [[invariants-and-traps]].

## See also
- [[post-base]] · [[social-publishing]] · [[legacy-qt-ui]]
