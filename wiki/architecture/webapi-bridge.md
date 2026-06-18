# webapi.Api — the pywebview bridge

`webapi.py` defines `Api`, passed to `webview.create_window(..., js_api=api)`. After
window creation `writerhelper.py` calls `api.set_window(window)` so methods can open
native dialogs. JS calls `await window.pywebview.api.<method>(...)` (wrapped as
`API.<method>` in `api.js`). All return JSON-serializable values.

## INVARIANT — no public data attributes on `Api`

State is held underscored: `self._articles`, `self._window`. pywebview's bridge
injection (`inject_pywebview` → `get_functions` in `webview/util.py`) walks `dir(api)`
and **recurses into every *public* non-callable attribute** to expose it to JS. A public
`window` reference sends it into `window.native` (the .NET WinForms Form) →
`AccessibilityObject.Bounds` → `Rectangle.Empty.Empty…` forever (pythonnet returns a
fresh wrapper each hop, so the `id()` cycle-guard never trips) → "maximum recursion
depth exceeded" on startup. Underscored names are skipped; **methods are safe** (recorded,
not recursed). Never add a public data attribute to `Api`. (QML never hit this — Qt
doesn't introspect the bridge object.) See [[invariants-and-traps]].

## Methods

| Method | Returns | Notes |
|---|---|---|
| `get_state(hl)` | dict | Everything the UI renders for one language (below). |
| `set_field(hl, field, value)` | True | Routes to the `ArticleModel` setter. Fields: title, content, date, tags, excerpt_image, posts_folder, website_url, **facets** (list), **draft** (bool), green, black. facets/draft are pair-shared. |
| `set_link(hl, name, url)` | True | Upsert a link slot. |
| `tag_suggestions(hl)` | `{matching, popular}` | Tag-picker chips: `matching` = vocabulary ranked by co-occurrence with this article's facets, `popular` = overall frequency; disjoint, exclude applied + house tag. From `tag_index.py`. See [[tag-vocabulary]]. |
| `toggle_tag(hl, label)` | tags str | Add/remove one tag (idempotent per concept) via `set_tags`, so the twin pairs. |
| `new_article(hl, copy_current=False)` | True | copy_current=True → "Make V2". |
| `new_both_articles(hl, copy_current=False)` | True | |
| `open_article(hl)` | bool | Native file dialog via `window.create_file_dialog`. |
| `open_image(hl)` | bool | Native **image** file dialog; reads the file and hands it to `set_excerpt_img` as a `data:` URL so it runs the self-hosting hook (→ webp). False on cancel. Drag-drop skips this — JS reads the file and calls `set_field(hl,'excerpt_image',<data url>)`. See [[astro-format]]. |
| `open_prev_article(hl)` / `open_next_article(hl)` | True | |
| `translate(hl)` | bool | → `ArticlesModel.translate`. |
| `prepare_post(hl, platform)` | dict | No side effects — popup data. Includes `facets_ok` (≥1 facet) + thread seed (`thread_text`/`thread_count`/`separator`). |
| `publish(hl, platform, mode, message, options=None)` | `{ok,url,error}` | Sends. `mode` ∈ text/thread/image; `options={"number","image"}` for thread, `{"image_url"}` for Instagram (image-only) ([[social-publishing]]). |
| `clear_link(hl, platform)` | True | Clears the slot to allow re-post. |
| `publish_instagram_image(hl)` | `{ok,public_url,log,error}` | Instagram **step 1**: copies the grabbed JPEG into the site repo + git-pushes it so a public raw URL exists ([[instagram-adapter]]). The popup then calls `publish(hl,"instagram","image",caption,{image_url})`. |
| `save_capture(hl, page, data_url)` | filename | Writes the JPEG `richTextArea_<slug>_<hl><page>.jpg` (CWD), name from `publishing.capture_filename` — slug-tied to the article. |
| `open_url(url)` | True | Opens in the system browser. |

## `get_state(hl)` shape

`hl, title, content, date, tags, excerpt_image, excerpt_image_local, posts_folder,
website_url, slug, post_url, facets, all_facets, draft, translation_key, green, black,
title_color, length_short, links[], content_md, content_md_separators,
content_md_separators_br, content_short, watermark`.

`facets` is the selected list, `all_facets` the five available (`serializers.FACETS`);
`post_url` is the public Astro URL; `content_md` is the Astro file.
`links[]` is `{name, url, publish}` (`publish` = `"x"`/`"facebook"`/`"instagram"`/`"bluesky"`/`""`); slot
visibility + the publish flag come from `LINK_SLOTS`, with the "Based on"/"Basé sur"
slot appended dynamically ([[link-slots]]). `excerpt_image_local` is a `data:` URL so the
card `<img>` renders and html2canvas can capture without tainting the canvas.

## See also
- [[web-ui]] · [[article-model]] · [[social-publishing]] · [[auto-save-and-pull-ui]]
