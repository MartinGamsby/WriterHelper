# Facebook — `post_fb.PostFB`

⚠️ This adapter does NOT inherit from `Post`. It predates the base class.
⚠️ It is NOT wired into the QML UI. FB posting is currently manual via the [CheckList](../ui/checklist.md).

## Config

`fb_settings_<hl>.ini`:

```ini
[Access]
token = <page-access-token>
pageid = <page-id>
```

Note the INI filename prefix (`fb_settings_` vs the `settings_<platform>_` pattern used by the newer adapters).

## API

Uses Facebook Graph API v18.0 directly via `requests.post`:

```python
def post_to_fb_page(self, msg, image_url):
    if image_url:
        url = f'https://graph.facebook.com/v18.0/{self.get_page_id()}/photos'
        payload = {'message': msg, 'access_token': self.get_token(), 'url': image_url}
    else:
        url = f'https://graph.facebook.com/v18.0/{self.get_page_id()}/feed'
        payload = {'message': msg, 'access_token': self.get_token()}
    r = requests.post(url, data=payload)
    data = r.json()
    return 'id' in data    # bool, not a URL
```

Differences vs the modern adapters:
- Method is `post_to_fb_page` not `post`.
- Returns `bool`, not a URL (so it cannot feed `ArticleModel.set_link` directly).
- Takes `image_url` (remote URL), not a local file path.

## To integrate later

If/when FB is wired in:
- Either subclass `Post` and rename `post_to_fb_page` → `post`, returning a constructed URL like the others.
- Or keep the old shape and add a separate routing path on `ArticleModel`.

## See also
- [post-base.md](post-base.md)
- [summary.md](summary.md)
- [../ui/checklist.md](../ui/checklist.md)
- [../practices.md](../practices.md)
