# Post Base Class

`post.py` defines `Post`, the inheritance base for new platform adapters.

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

    def write_default_config(self):
        with open(self.config_filename(), 'w') as f:
            self.config.write(f)
```

## Override contract

A new subclass must:
1. Pass an `access=...` dict to `super().__init__` describing the INI fields it needs.
2. Override `config_filename` to point at `settings_<platform>_<hl>.ini`.
3. Override `post(msg, image_local_url, alt_text)` to do the actual API call and return the resulting public URL.

If `config_filename` is forgotten, the base writes `settings_TODO_<hl>.ini` on first run — that's the easy-to-spot signal.

## INI shape

Always a single `[Access]` section. Field names are inherited from the `access` dict the subclass passes in. Examples:
- `PostBsky` → `Handle`, `AppPassword` → `settings_bsky_<hl>.ini`
- `PostX` → `Handle`, `APIKey`, `APISecret`, `BearerToken`, `AccessToken`, `AccessSecret`, `ClientID`, `ClientSecret` → `settings_x_<hl>.ini`

## post() contract

`post(msg, image_local_url, alt_text) -> str` (returns the public URL of the posted item).

`msg` is the text body. `image_local_url` is a local file path (or None for text-only). `alt_text` is what's used for the image's alt text on platforms that support it (Bluesky does; X v2 currently does not pass it).

## See also
- [summary.md](summary.md)
- [bluesky.md](bluesky.md)
- [x.md](x.md)
- [../model/post-routing.md](../model/post-routing.md)
