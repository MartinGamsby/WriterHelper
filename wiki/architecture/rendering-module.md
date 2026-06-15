# rendering.py

Stateless module of pure functions producing the HTML [[content-flavors]] from an
`article`. [[article-model]] exposes thin `content_md*()` methods that delegate here, so
callers can use either. No Qt, no state of its own.

## What it provides

- `content_md_rich(article)` — markdown→HTML via the `markdown` library + link/paragraph
  styling.
- `content_md_separators(article)` — the styled image-card HTML (captured to PNG,
  [[image-card-capture]]).
- `content_md_separators_br(article)` — the social-post HTML (`<br/>` decoration +
  hashtags).
- `content_short(article)` — title-only + hashtags.
- `plain_text(article)` — BeautifulSoup-stripped text, no hashtags — the exact post
  text used for the [[social-publishing]] char count.
- `footer_md(article)` — `- [text](url)` lines for non-empty links ([[link-slots]]).
- `hashtags(article)`, `categories(article)` (legacy-only), `excerpt_image_file`
  (resolves the excerpt image to a **local filesystem path**, or "" when remote/data/not
  found — used to attach the article image to a post, [[social-publishing]]) and
  `excerpt_image_local` (the same file as a `data:` URL so the webview / html2canvas can
  use it without tainting the canvas; falls back to the raw value when not local).
- `templated(template, article)` + `load_templates()` — the placeholder substitution
  engine ([[templates]]).

`content_md` itself is **not** here — the saved file is built by [[serializers]]
(`serialize`).

## See also
- [[content-flavors]] — the five shapes and their decoration specifics
- [[templates]] — the placeholder vocabulary
- [[article-model]] — the delegating methods
