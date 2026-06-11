# Content Rendering — the Five Flavors

`ArticleModel` exposes the same article data in five shapes. All are Qt `Property`s (notify=updated), so each rendered flavor refreshes whenever any input changes.

| Flavor | Template | HTML? | Used by |
|---|---|---|---|
| `content_md` | `templates/post.md` | No | What gets written to disk (Jekyll post). Always. |
| `content_md_rich` | `post_content_only.md` then `markdown.markdown(...)` | Yes | The Qt rich-text preview (`TextArea` with `textFormat: TextEdit.RichText`) |
| `content_md_separators` | `post_content_only.md` + extra HTML decoration | Yes | The image surface — the `richTextArea` Rectangle that's captured to PNG |
| `content_md_separators_br` | `post_content_only.md` + `<br/>` decoration + hashtags | Yes | The social-post text body (when it fits the platform character limit) |
| `content_short` | `post_title_only.md` + hashtags | Yes | A title-only fallback rendering |

## What each one does (specifics)

### `content_md`
Uses the full `templates/post.md` (Jekyll frontmatter + body + footer). No HTML conversion. This is what `on_updated` writes to `<posts>/<YYYY-MM-DD>-<slug>.md`.

### `content_md_rich`
Markdown→HTML via the `markdown` library, then:
- `<a` gets `style='color:<title-color>'`.
- `<p>` gets `style='text-indent: 50px;'`.
Title-color is `#ade6b9` if `green`, else `white` if `black`, else `black`.

### `content_md_separators`
Built on `content_md_rich`. Adds, in order:
- A floating right-side `<table>` with the local excerpt image (`excerpt_image_local()` — `file:///` URL if the image exists locally as `<posts>/../<image>`, else the bare path).
- `<h4>` → centered.
- `<blockquote><p>` → indented `-7px` and wrapped in `<i><b>`.
- `<h1>`, `<h2>`, `<h3>` → centered, colored with title-color.
- `<h4>` → colored with title-color.

This is the version captured to PNG.

### `content_md_separators_br`
Built on `content_md_rich`. Adds:
- `<h3>`, `<h4>` → centered with trailing colon.
- `<li>` → prefixed with `- `.
- Same blockquote treatment as above.
- `</h1>`, `</h2>`, `</p>`, `</blockquote>` → followed by `<br />`.

After the HTML, appends one `#tag` line per non-`Gamsblurb` tag (lowercased, unidecoded, non-alphanumeric stripped, spaces removed).

### `content_short`
Just the `post_title_only.md` template (which is `### **<TITLE>**`) → markdown → `<br />` + the hashtag block.

## Templating contract

All five go through `templated(template)` which substitutes:
- `<TITLE>` → `self.title`
- `<EXCERPT_IMAGE>` → `self.excerpt_image`
- `<CONTENT>` → `self.content`
- `<TAGS>` → `self.get_tags()`
- `<FOOTER>` → `footer_md()` (one `- [text](url)\n` line per non-empty link)
- `<CATEGORIES>` → `categories()` — `["Length: <Mini|Short|Medium>", "Gamsblurb"]` rendered as a JSON-style array of double-quoted strings
- `<REF>` → `ref.website_url + ref.slug` (the paired other-language URL)

If `posts_folder` is not a real directory, `templated` returns `"<path> is not a folder"` instead — visible in the preview as a clue.

## See also
- [article-model.md](article-model.md)
- [../templates/summary.md](../templates/summary.md)
- [../ui/image-capture.md](../ui/image-capture.md) — what consumes `content_md_separators`
- [post-routing.md](post-routing.md) — what consumes `content_md_separators_br`
