# Templates — Summary

`templates/` holds the markdown templates. The four loaded by
`rendering.load_templates` are rendered by `templated(template)` (fixed placeholder
vocabulary). `post_astro.md` is a **reference** only — the written Astro file is built
in code by `serializers.serialize` (the optional `draft`/`image` lines and footer
block are conditional), not via `templated`.

## The files

| File | Used by | What's in it |
|---|---|---|
| `post_astro.md` | reference for `serializers.serialize` (the **saved** file) | Astro frontmatter (no `layout`/`categories`, `translationKey`, `facets`, optional `draft`/`image`) + `<CONTENT>` (no title heading) + `---` + `<FOOTER>` |
| `post.md` | legacy Jekyll write (no longer used; format is load-only) | Full Jekyll frontmatter + `### **<TITLE>**` heading + `<CONTENT>` + `---` + `<FOOTER>` |
| `post_content.md` | (currently unused; older `content_md_rich` path) | `### **<TITLE>**` + `<CONTENT>` + `---` + `<FOOTER>` (no frontmatter) |
| `post_content_only.md` | `content_md_rich`, `content_md_separators`, `content_md_separators_br` (i.e. the rich/HTML flavors) | `### **<TITLE>**` + `<CONTENT>` (no footer, no separator) |
| `post_title_only.md` | `content_short` | `### **<TITLE>**` only |

The rich/HTML card flavors (`post_content_only.md`, `post_title_only.md`) still
include the `### **<TITLE>**` heading — they render the visual image card, which is
independent of the saved file format.

## Placeholder vocabulary

Recognized by `ArticleModel.templated`:

| Placeholder | Resolves to |
|---|---|
| `<TITLE>` | `self.title` |
| `<EXCERPT_IMAGE>` | `self.excerpt_image` (relative path) |
| `<CONTENT>` | `self.content` (raw markdown body) |
| `<TAGS>` | `self.get_tags()` — comma-separated string |
| `<FOOTER>` | `footer_md()` — `- [text](url)\n` lines for non-empty links |
| `<CATEGORIES>` | `categories()` — JSON-style `["Length: X", "Gamsblurb"]` |
| `<REF>` | `ref.website_url + ref.slug` — URL of the paired other-language article |

Placeholders are plain string `replace()` — order in `templated` is `TITLE → EXCERPT_IMAGE → CONTENT → TAGS → FOOTER → CATEGORIES → REF`. If a placeholder name ever overlaps with rendered content, the literal substitution will leak — keep the angle-bracket form distinct.

## post.md (full Jekyll)

```markdown
---
layout: post
title: "<TITLE>"
categories: <CATEGORIES>
tags: [<TAGS>]
excerpt_image: <EXCERPT_IMAGE>
ref: <REF>

---

### **<TITLE>**

<CONTENT>

---

<FOOTER>
```

The double-dashed separators are load-bearing: `change_article` splits on `---` and expects 3 or 4 parts.

## Guard

If `posts_folder` is not a real directory, `templated` returns `"<path> is not a folder"` instead of a rendered template — visible in the QML previews as a debugging hint.

## See also
- [../model/rendering.md](../model/rendering.md)
- [../file-storage/jekyll-format.md](../file-storage/jekyll-format.md)
