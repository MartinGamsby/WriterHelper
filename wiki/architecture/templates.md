# Templates (`templates/`)

Markdown templates. The four loaded by `rendering.load_templates` are rendered by
`templated(template)` with a fixed placeholder vocabulary ([[rendering-module]]).
`post_astro.md` is a **reference** only — the saved Astro file is built in code by
[[serializers]] `serialize` (conditional `draft`/`image`/footer lines), not via
`templated`.

## The files

| File | Used by | Contents |
|---|---|---|
| `post_astro.md` | reference for `serialize` (the **saved** file) | Astro frontmatter (no `layout`/`categories`; `translationKey`, `facets`, optional `draft`/`image`) + `<CONTENT>` (no title heading) + `---` + `<FOOTER>` |
| `post.md` | legacy Jekyll write (no longer used) | Full Jekyll frontmatter + `### **<TITLE>**` + `<CONTENT>` + `---` + `<FOOTER>` |
| `post_content.md` | unused (older `content_md_rich` path) | `### **<TITLE>**` + `<CONTENT>` + `---` + `<FOOTER>` |
| `post_content_only.md` | the rich/HTML flavors | `### **<TITLE>**` + `<CONTENT>` |
| `post_title_only.md` | `content_short` | `### **<TITLE>**` only |

The rich/HTML card flavors keep the `### **<TITLE>**` heading — they render the visual
image card, independent of the saved file format ([[content-flavors]]).

## Placeholder vocabulary

Recognized by `templated`: `<TITLE>`, `<EXCERPT_IMAGE>`, `<CONTENT>`, `<TAGS>`,
`<FOOTER>` (link lines), `<CATEGORIES>` (legacy `["Length: X", "Gamsblurb"]`), `<REF>`
(paired other-language URL). Plain string `replace()` in order TITLE → EXCERPT_IMAGE →
CONTENT → TAGS → FOOTER → CATEGORIES → REF. The double-dashed `---` separators in
`post.md` are load-bearing — [[jekyll-format]] load splits on `---`.

Guard: if `posts_folder` isn't a real directory, `templated` returns `"<path> is not a
folder"` — a debugging hint surfaced in the previews.

## See also
- [[rendering-module]] · [[content-flavors]] · [[jekyll-format]] · [[astro-format]]
