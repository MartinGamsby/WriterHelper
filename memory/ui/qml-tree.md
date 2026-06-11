# QML Tree

`ui/qml/` contains the entire UI. PySide6 only loads `main.qml`; the others are referenced as components.

## main.qml

`Window` 1800x1024, title `"Writer Helper"`, Material accent `Teal`. Exposes `property QtObject backend` set from Python after engine load.

Layout:
- Top bar: green strip with title label + two `CheckBox`es (`cbFR`, `cbEN`) controlling column visibility.
- Middle `RowLayout`:
  - `CheckList { width: 160 }` (leftmost sidebar)
  - For each visible language, in order FR-meta / FR-content / EN-content / EN-meta:
    - `ArticleMeta { hl: "fr"|"en" }` (220 or 320 wide)
    - `ArticleContent { hl: "fr"|"en" }` (640 or 1024 wide)
    - Vertical green `Separator` rectangles between them
- Bottom: a `Label` showing current date/time in `fr_CA` locale, refreshed by a 1-second `Timer`.

## ArticleContent.qml (~500 lines)

The main per-language editor + image-capture surface. `Flickable` containing:
1. Header row: length label, "<hl> Article" title, character/word counter, posts-folder TextField, website-URL TextField.
2. `Setting` row: title TextField + "Date override" checkbox/TextField.
3. Plain content `TextArea` (`contentEdit`, 320 tall) — what the user types.
4. Controls row: Font SpinBox, Green/Black checkboxes, W/H SpinBoxes, "Center" checkbox.
5. Buttons row: `Grab` / `Adjust` / `Square` / `Portrait` / `Landscape` / `500x400`. See [image-capture.md](image-capture.md).
6. Hidden `Rectangle` (`visible: false`) with another rich-text preview.
7. `TextArea` showing `p_content_short` (title + hashtags).
8. The capturable `Rectangle` (`id: richTextArea`) — colored by green/black checkboxes; contains an inner `contentBg` with the rich-text body (`p_content_md_separators`), a "linktr.ee/..." watermark (per `hl`), and a page-number label visible when content overflows.
9. Tail `TextArea` showing `p_content_md_separators_br` (the social-post preview).
10. Tail `Flickable` showing `p_content_md` (the raw Jekyll file).
11. Periodic 2-second `Timer` that flushes focus into `set_title` / `set_content` if the field has focus. This is a fallback to `onEditingFinished` — captures unsaved typing if the user does not blur the field.

## ArticleMeta.qml

Per-language metadata panel. `Flickable` with:
- Button grid: `New`, `Translate`, `Open`, `Make V2`, `Open Prev`, `Open Next`, `New both articles`.
- `Setting "Image"` — TextField for `excerpt_image`.
- `Setting "Links"` — grid of label/TextField rows for each link slot (see [../model/links.md](../model/links.md)). The `X/Twitter` and `Bluesky` labels are rich-text `<a>`s whose `onLinkActivated` calls `hl_model.post_x()` / `hl_model.post_bluesky()` — these are how social posts are triggered.
- `Setting "Tags"` — TextField + a (currently inert) "used tags" description; `Backend.get_used_tags(hl)` is wired but returns `""` early-out.
- `Button "Generate Tags"` — calls `hl_model.generate_tags()` which is a `print("generate_tags")` stub.

## CheckList.qml

A static list of `WordWrapCheckBox`es and link labels — the manual authoring workflow checklist. Not persisted, not data-bound. See [checklist.md](checklist.md).

## Setting.qml

Reusable container: a row with optional `name` label, `desc` sublabel, and a `default property` slot for the child content. Used by `ArticleContent` (title) and `ArticleMeta` (Image, Links, Tags).

## WordWrapCheckBox.qml

A `CheckBox` whose label wraps. Used only by `CheckList.qml`.

## Bindings cheat-sheet

| Binding | Reads from | Triggered by |
|---|---|---|
| `hl_model.p_title` | `ArticleModel.title` | `updated` signal |
| `hl_model.p_content` | `ArticleModel.content` | `updated` |
| `hl_model.p_content_md_separators` | rendered HTML | `updated` |
| `hl_model.p_content_md_separators_br` | rendered HTML | `updated` |
| `hl_model.p_content_md` | full Jekyll | `updated` |
| `hl_model.p_link_*` | named link slot | `updated` |
| `hl_model.p_posts_folder`, `p_website_url` | INI | `updated` |
| Click `Translate` button | calls `root.backend.translate(hl)` | n/a |
| Click `X/Twitter` link label | calls `hl_model.post_x()` | n/a |
| Click `Bluesky` link label | calls `hl_model.post_bluesky()` | n/a |

## See also
- [../model/article-model.md](../model/article-model.md)
- [image-capture.md](image-capture.md)
- [checklist.md](checklist.md)
