# Content flavors — the five renderings

One article, five shapes. The four HTML flavors are pure functions in `rendering.py`
taking an `article`; [[article-model]] exposes thin `content_md*()` methods that
delegate. The fifth, `content_md`, is the saved file via [[serializers]] — not a
`rendering.py` template. The web UI injects the HTML flavors as `innerHTML`.

| Flavor | Built from | HTML? | Used by |
|---|---|---|---|
| `content_md` | `serializers.serialize` | No | The saved [[astro-format]] file. Always. |
| `content_md_rich` | `post_content_only.md` → `markdown.markdown` | Yes | Base for the other HTML flavors; rich preview |
| `content_md_separators` | `content_md_rich` + decoration | Yes | The image card (`.card-frame`), captured to JPEG ([[image-card-capture]]) |
| `content_md_separators_br` | `content_md_rich` + `<br/>` + hashtags | Yes | Source of social-post text (`rendering.plain_text` strips it for the char count, see [[social-publishing]]) |
| `content_short` | `post_title_only.md` + hashtags | Yes | Title-only fallback rendering |

`rendering.py` also provides `plain_text(article)` (BeautifulSoup-stripped, no
hashtags — the exact post text), `footer_md`, `categories` (legacy-only now),
`hashtags`, and `excerpt_image_local` (embeds a local image as a `data:` URL so the
webview / html2canvas can use it without tainting the canvas).

## Decoration specifics

- **`content_md_rich`** — `<a>` gets `style='color:<title-color>'`; `<p>` gets
  `text-indent:50px`. Title-color = `#ade6b9` (green) / white (black) / black (neither).
- **`content_md_separators`** (the captured card) — adds a floating right `<table>`
  with the local excerpt image; centers `<h4>`; indents `<blockquote><p>` `-7px` wrapped
  in `<i><b>`; centers + colors `<h1..h3>` and colors `<h4>`.
- **`content_md_separators_br`** (the social text) — centers `<h3>/<h4>` with a trailing
  colon; prefixes `<li>` with `- `; same blockquote treatment; appends `<br/>` after
  `</h1> </h2> </p> </blockquote>`; then one `#tag` line per non-`Gamsblurb` tag
  (lowercased, unidecoded, stripped).
- **`content_short`** — `### **<TITLE>**` → markdown → `<br/>` + the hashtag block.

## Templating contract

The HTML flavors go through `templated(template)` (in `rendering.py` / [[templates]]),
substituting `<TITLE>`, `<EXCERPT_IMAGE>`, `<CONTENT>`, `<TAGS>`, `<FOOTER>`,
`<CATEGORIES>`, `<REF>`. If `posts_folder` isn't a real directory, `templated` returns
`"<path> is not a folder"` — a debugging clue surfaced in the preview.

## See also
- [[rendering-module]] — the module reference
- [[templates]] — the markdown templates + placeholder vocabulary
- [[image-card-capture]] — consumes `content_md_separators`
- [[social-publishing]] — consumes `content_md_separators_br`
