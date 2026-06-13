# Astro post format

The **written** format. WriterHelper emits posts for the bilingual Astro site
[[martingamsby-site]] (`src/content/blog/<hl>/`). Hard switch, no dual-write: saving
writes Astro only. [[jekyll-format]] is load-only legacy. Serializer: [[serializers]].

## Anatomy

```markdown
---
title: "Sample Title"
date: 2026-06-13
translationKey: 2026-06-13-sample-title
facets: [dev, ideas]
tags: [Gamsblurb]
draft: true
image: /assets/posts/2026-06-13-sample-title.header.webp
imageThumb: /assets/posts/2026-06-13-sample-title.thumb.webp
---

Body markdown — NO `### **<TITLE>**` heading (the site layout renders the title).

---

- [X/Twitter](https://x.com/...)
```

Enforced site-side by `src/content.config.ts` zod schema.

## Field semantics

| Field | Source | Notes |
|---|---|---|
| `title` | `title` | double-quoted |
| `date` | `date` | bare `YYYY-MM-DD` |
| `translationKey` | `get_translation_key()` | sticky pairing key — [[bilingual-pairing]] |
| `facets` | `facets` | bare flow list `[dev, ideas]`; `[]` when empty (but WriterHelper requires ≥1 to publish) |
| `tags` | `get_tags()` | bare `[Gamsblurb,Vie]` (raw comma string) |
| `draft` | `draft` | emitted `draft: true` ONLY when True; omitted to publish |
| `image` | `excerpt_image` | header/OG image; emitted only when non-empty; a local `…header.webp` once self-hosted |
| `imageThumb` | `image_thumb` | 160² list thumbnail; emitted only alongside a self-hosted `image`; round-tripped on load so edits never strip it |
| body | `content` | no title heading |
| footer | `footer_md()` | `- [text](url)` lines; whole `---` + footer block omitted when no links |

`categories` is intentionally dropped (the length label is derivable; `Gamsblurb`
survives as a tag).

## Filename & URL

`<YYYY-MM-DD>-<slug>.md`; the file **stem is the public URL slug**: `/<lang>/blog/<stem>/`.
`get_slug()` drives the filename. Public URL via `get_post_url()` =
`<website><date>-<slug>/`, where `[URLs] website` is the Astro base
(`https://martingamsby.com/<hl>/blog/`). Social posts and the "Based on" link share this
URL.

## translationKey (sticky, stamped on both)

The identical literal value in both languages' files. Minted `<date>-<EN-slug>` (own
slug fallback while EN untitled), stamped onto BOTH `self` and `ref` at mint so the
files can't diverge by authoring order; frozen once set; getter never touches disk. Full
rules + the self-heal-on-load behavior: [[bilingual-pairing]].

## Load: format auto-detection

`parse` reads frontmatter then routes Jekyll (`layout: post` / `ref:`) vs Astro. Astro
body/footer split uses the **last** `\n---\n`. `delete_last` forced False during load.
See [[serializers]].

## Image self-hosting (localize hook)

Preview images are **self-hosted, never hot-linked**. `set_excerpt_img(text)` may
receive any URL; after the normal save, `ArticleModel._localize_excerpt_image()` runs —
ONLY when the value is remote (`localize.is_remote`: http/https, protocol-relative,
`data:`; local paths left alone, keeping tests offline).

`localize.py` shells out to the site's hook
`node tools/localize-images.mjs --file <that post.md>` (finding the [[martingamsby-site]]
checkout by walking up from the posts folder until `tools/localize-images.mjs` is
found). That tool downloads the image, writes a large `…header.webp` + a 160²
`…thumb.webp` under `public/assets/posts/`, and rewrites the file's frontmatter. The
bridge then reads the new `image:`/`imageThumb:` back onto the model, so later saves
re-emit local paths. Naming-scheme-agnostic (the bridge reads whatever the tool wrote)
and best-effort: if node / the tool / the network is unavailable it logs and leaves the
remote URL (still renders). Idempotent — a local value is skipped.

## See also
- [[serializers]] · [[jekyll-format]] · [[file-storage]] · [[bilingual-pairing]] · [[templates]]
