# Post base class (`post.py`)

`Post` is the inheritance base for new platform adapters. `PostBsky`
([[bluesky-adapter]]), `PostX` ([[x-adapter]]), `PostFB` ([[facebook-adapter]]), and
`PostIG` ([[instagram-adapter]]) inherit it. (`PostFB` predated the base and was rewritten
onto it; it skips the optional `post_thread` override — text/image only. `PostIG` is
image-only and takes a **public `image_url`** instead of a local upload — see below.)

## Class shape

```python
class Post:
    def __init__(self, hl, access={'Handle': '<TODO>', 'AppPassword': '<TODO>'}):
        self.hl = hl
        self.config = configparser.ConfigParser()
        self.config['Access'] = access
        self.load_config()

    def get_handle(self):       return self.config["Access"]["Handle"]
    def get_app_password(self): return self.config["Access"]["AppPassword"]

    def post(self, msg, image_local_url, alt_text):
        print("To implement")

    def config_filename(self):
        return 'settings_TODO_%s.ini' % self.hl    # smoke signal — subclass forgot to override

    def load_config(self):
        if os.path.isfile(self.config_filename()):
            self.config.read(self.config_filename())
        else:
            self.write_default_config()
```

## Override contract

A new subclass must:
1. Pass an `access=...` dict to `super().__init__` describing its INI fields.
2. Override `config_filename` → `settings_<platform>_<hl>.ini`.
3. Override `post(msg, image_local_url, alt_text)` → do the API call, return the public
   URL.
4. Override `post_thread(messages, image_local_url, alt_text) → [url]` → post a reply
   chain (image attaches to the first post only). The base raises `NotImplementedError`
   (no generic reply mechanism). Used by Thread mode ([[social-publishing]],
   [[thread-split]]).

If `config_filename` is forgotten, the base writes `settings_TODO_<hl>.ini` on first run
— the easy-to-spot signal ([[invariants-and-traps]]).

## INI shape

Always one `[Access]` section; field names come from the subclass's `access` dict
(stored git-ignored, [[secrets]]):
- `PostBsky` → `Handle`, `AppPassword` → `settings_bsky_<hl>.ini`
- `PostX` → `Handle`, `APIKey`, `APISecret`, `BearerToken`, `AccessToken`,
  `AccessSecret`, `ClientID`, `ClientSecret` → `settings_x_<hl>.ini`

## post() contract

`post(msg, image_local_url, alt_text, embed_url=None) → str` (the public URL). `msg` =
text body, `image_local_url` = local file path or None, `alt_text` = image alt where
supported (Bluesky yes; X v2 currently doesn't attach it). `embed_url` requests an
external link-preview card; only [[bluesky-adapter]] acts on it (X/Facebook auto-unfurl
links, so they accept and ignore it). `post_thread` takes the same `embed_url` (card on
the first post). The base/PostX/PostFB signatures all carry it so the `publishing.py` call
site stays uniform.

`PostIG` ([[instagram-adapter]]) adds an `image_url=None` kwarg and **ignores
`image_local_url`/`embed_url`**: Instagram fetches a public image URL server-side rather
than accepting a local upload, so `publishing._publish_instagram` calls
`post(msg=caption, image_url=<public URL>)` after a separate step makes that URL public.

## See also
- [[bluesky-adapter]] · [[x-adapter]] · [[publishing]] · [[social-publishing]]
