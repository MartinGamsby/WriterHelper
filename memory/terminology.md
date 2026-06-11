# Terminology

- **article** — one blog post. Has title, content (markdown), tags, excerpt image, optional links, date. Persisted as one `.md` file in the configured `posts` folder.
- **hl** — language code (`"fr"` or `"en"`). Threads through everything: model selection, INI filenames, PNG output names, translate direction.
- **ref** — the reciprocal article in the *other* language. `ArticleModel.set_ref(other)` couples FR↔EN. The `<REF>` placeholder in the Jekyll frontmatter resolves to the website URL of the paired article (`<ref.website_url><ref.slug>`).
- **slug** — kebab-case identifier derived from `title` via `unidecode` → lowercase → strip non-alphanumeric (preserves `-`). Used in the filename `YYYY-MM-DD-<slug>.md`. Code: `ArticleModel.get_slug`.
- **length category** — `mini` if `len(content) < 280`, `medium` if `> 2000`, else `short`. Surfaces in UI label ("Length: Short" / "Longueur: Court"), in the Jekyll `categories` array, and indirectly gates the social-post text-vs-image fallback (the platform character limit, not the category itself, makes the call). See [model/post-routing.md](model/post-routing.md).
- **excerpt_image** — relative path stored in Jekyll frontmatter. Resolved locally as `<posts>/../<image>` (`Path(posts).parent`) for the Qt rich-text preview only.
- **link** — a `(text, url)` pair in `ArticleModel.links`. Named slots: Medium, Typeshare, X/Twitter, LinkedIn, Facebook, Bluesky, YouTube, YouTube Shorts, Source, "Based on" / "Basé sur". See [model/links.md](model/links.md).
- **content_md flavors** — the five renderings of one article: `content_md` (full Jekyll), `content_md_rich` (HTML for Qt), `content_md_separators` (styled HTML for the image surface), `content_md_separators_br` (line-broken for socials), `content_short` (title-only + hashtags). See [model/rendering.md](model/rendering.md).
- **richTextArea PNG** — `richTextArea_<hl><N>.png` saved by QML `grabToImage`. `<N>` is the 1-indexed page count for content longer than one screen. Consumed by the social-post fallback when plain text exceeds the platform limit. Page 1 is what the fallback uses.
- **Post (base) vs PostFB** — `post.py` `Post` is the inheritance base for `PostBsky` and `PostX`. `PostFB` predates it and does NOT inherit. See [posting/post-base.md](posting/post-base.md).
- **delete_last** — `ArticleModel` flag (default True). When True, saving a new filename deletes the previously-saved file (rename-by-delete-and-write). Toggled False around `new_article`, `change_article`, and `new_both_articles` to avoid clobbering during transitions.
- **DEFAULT_TAGS** — module-level constant in `model.py`: `"Gamsblurb"`. Used as the seed tag value on new articles and as the always-present site category.
- **Gamsblurb** — the site's house category/tag. Always present. The "categories" array in frontmatter is `[<length-category>, "Gamsblurb"]`.

## See also
- [summary.md](summary.md)
- [practices.md](practices.md)
