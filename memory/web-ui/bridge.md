# Bridge — `webapi.Api`

`webapi.py` defines `Api`, passed to `webview.create_window(..., js_api=api)`. After window creation `writerhelper.py` calls `api.set_window(window)` so methods can open native dialogs.

**INVARIANT — no public data attributes on `Api`.** Its state is held as `self._articles` and `self._window` (underscored). pywebview's bridge injection walks `dir(api)` and recurses into every *public* non-callable attribute; a public `window` reference leads it into `window.native` (.NET Form) → infinite recursion → startup crash. Underscored names are skipped. Methods are safe (recorded, not recursed). See [startup-freeze.md](startup-freeze.md).

JS calls `await window.pywebview.api.<method>(...)` (wrapped as `API.<method>(...)` in `api.js`). All return JSON-serializable values.

## Methods

| Method | Returns | Notes |
|---|---|---|
| `get_state(hl)` | dict | Everything the UI renders for one language (see below). |
| `set_field(hl, field, value)` | True | Routes to the matching `ArticleModel` setter. Fields: title, content, date, tags, excerpt_image, posts_folder, website_url, **facets** (list), **draft** (bool), green, black. `facets`/`draft` are pair-shared (mirror to the twin). |
| `set_link(hl, name, url)` | True | Upsert a link slot. |
| `new_article(hl, copy_current=False)` | True | copy_current=True → "Make V2". |
| `new_both_articles(hl, copy_current=False)` | True | |
| `open_article(hl)` | bool | Native file dialog via `window.create_file_dialog`. |
| `open_prev_article(hl)` / `open_next_article(hl)` | True | |
| `translate(hl)` | bool | Delegates to `ArticlesModel.translate`. |
| `prepare_post(hl, platform)` | dict | No side effects — popup data. Includes `facets_ok` (≥1 facet). |
| `publish(hl, platform, mode, message)` | dict `{ok,url,error}` | Sends. |
| `clear_link(hl, platform)` | True | Clears the platform's link slot to allow re-post. |
| `save_capture(hl, page, data_url)` | filename | Writes `richTextArea_<hl><page>.png` (CWD). |
| `open_url(url)` | True | Opens in system browser. |

## `get_state(hl)` shape
`hl, title, content, date, tags, excerpt_image, excerpt_image_local, posts_folder, website_url, slug, post_url, facets, all_facets, draft, translation_key, green, black, title_color, length_short, links[], content_md, content_md_separators, content_md_separators_br, content_short, watermark`.

`facets` is the selected list, `all_facets` the five available (`serializers.FACETS`) for rendering checkboxes; `post_url` is the public Astro URL; `content_md` is now the Astro file.

`links[]` is `{name, url, publish}` — `publish` is `"x"`/`"bluesky"`/`""`. Slot visibility per `hl` and the `publish` flag come from `LINK_SLOTS` in `webapi.py`; the `Based on`/`Basé sur` slot is appended dynamically.

`excerpt_image_local` is a `data:` URL (via `rendering.excerpt_image_local`) so the card `<img>` renders and html2canvas can capture it without tainting the canvas.

## See also
- [summary.md](summary.md)
- [../model/article-model.md](../model/article-model.md)
- [../posting/popup-flow.md](../posting/popup-flow.md)
