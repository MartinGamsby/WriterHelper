# Terminology

- **article** — one blog post. Has title, content (markdown), tags, excerpt image, optional links, date. Persisted as one `.md` file in the configured `posts` folder.
- **hl** — language code (`"fr"` or `"en"`). Threads through everything: model selection, INI filenames, PNG output names, translate direction.
- **ref** — the reciprocal article in the *other* language. `ArticleModel.set_ref(other)` couples FR↔EN. The `<REF>` placeholder in the Jekyll frontmatter resolves to the website URL of the paired article (`<ref.website_url><ref.slug>`).
- **slug** — kebab-case identifier derived from `title` via `unidecode` → lowercase → strip non-alphanumeric (preserves `-`). Used in the filename `YYYY-MM-DD-<slug>.md`. Code: `ArticleModel.get_slug`.
- **length category** — `mini` if `len(content) < 280`, `medium` if `> 2000`, else `short`. Surfaces in UI label ("Length: Short" / "Longueur: Court"), in the Jekyll `categories` array, and indirectly gates the social-post text-vs-image fallback (the platform character limit, not the category itself, makes the call). See [model/post-routing.md](model/post-routing.md).
- **excerpt_image** — relative path stored in Jekyll frontmatter. Resolved locally as `<posts>/../<image>` (`Path(posts).parent`) for the Qt rich-text preview only.
- **link** — a `(text, url)` pair in `ArticleModel.links`. Named slots: Medium, Typeshare, X/Twitter, LinkedIn, Facebook, Bluesky, YouTube, YouTube Shorts, Source, "Based on" / "Basé sur". See [model/links.md](model/links.md).
- **content_md flavors** — the five renderings of one article, now in `rendering.py`: `content_md` (full Jekyll), `content_md_rich` (HTML), `content_md_separators` (styled HTML for the image card), `content_md_separators_br` (line-broken for socials), `content_short` (title-only + hashtags). The web UI injects these as `innerHTML`. See [model/rendering.md](model/rendering.md).
- **richTextArea PNG** — `richTextArea_<hl><N>.png`. Now saved by the web UI: html2canvas captures the `.card-frame`, page by page, and `webapi.save_capture` writes each. `<N>` is the 1-indexed page count for content longer than one screen. Consumed by the publish image mode. Page 1 is what the fallback uses.
- **card / .card-frame** — the capturable branded image surface in the web UI (was the QML `richTextArea` Rectangle). Holds `content_md_separators`, a per-`hl` `linktr.ee` watermark, and a page-number badge when content overflows. Colored by the green/black checkboxes.
- **Post (base) vs PostFB** — `post.py` `Post` is the inheritance base for `PostBsky` and `PostX`. `PostFB` predates it and does NOT inherit. See [posting/post-base.md](posting/post-base.md).
- **prepare_post / publish** — the two-phase social-post flow in `publishing.py`. `prepare_post(article, platform)` computes what *would* be sent (text, char count, fits?, suggested mode, image preview) with NO side effects, feeding the confirmation popup. `publish(article, platform, mode, message)` actually sends the user-confirmed message. See [posting/popup-flow.md](posting/popup-flow.md).
- **mode (text vs image)** — the publish choice surfaced in the popup. `"text"` posts the message only; `"image"` posts the message + page-1 PNG (`richTextArea_<hl>1.png`). Defaulted from `suggested_mode` (text if the rendered plain text fits the platform limit, else image) but user-overridable.
- **bridge / webapi.Api** — the pywebview JS bridge. JS calls `window.pywebview.api.<method>(...)`; methods live on `webapi.Api`. UI is pull-based: after any mutation JS re-fetches `get_state(hl)` and re-renders. See [web-ui/bridge.md](web-ui/bridge.md).
- **save_capture** — bridge method that writes one html2canvas page as `richTextArea_<hl><page>.png` (CWD). Replaces the QML `grabToImage` callback; same output contract.
- **updated()** — `ArticleModel.updated()` is now a plain method (not a Qt Signal) called by every setter on real change; it re-saves the `.md` file. The JS layer drives re-render separately by re-fetching state.
- **delete_last** — `ArticleModel` flag (default True). When True, saving a new filename deletes the previously-saved file (rename-by-delete-and-write). Toggled False around `new_article`, `change_article`, and `new_both_articles` to avoid clobbering during transitions.
- **DEFAULT_TAGS** — module-level constant in `model.py`: `"Gamsblurb"`. Used as the seed tag value on new articles and as the always-present site category.
- **Gamsblurb** — the site's house category/tag. Always present. The "categories" array in frontmatter is `[<length-category>, "Gamsblurb"]`.

## See also
- [summary.md](summary.md)
- [practices.md](practices.md)
