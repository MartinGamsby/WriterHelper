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
| `title` | `title` | double-quoted; backslashes + `"` are escaped (`_yaml_dq`) so a quoted title — `I just watched "the Martian"` — stays valid YAML and round-trips |
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

### Importing a local file (drop / Browse) — same hook, no new mode

A user can also **drop an image** on the meta panel's image zone or pick one via
**Browse…**. Both turn the file into a `data:` URL — already a first-class
`localize.is_remote` value (the tool's `isExternal` and Node's `fetch` both resolve
`data:`) — and feed it straight to `set_excerpt_img`. So a dropped/opened file flows
through the *exact* path above: the data URL is written to frontmatter, the hook decodes
it into the slug-named webp pair, and the local paths are read back. No image-specific
branch exists in the model. Browse reads the file in Python (`webapi.open_image` →
`localize.file_to_data_url`); drag-drop reads it in JS and calls
`set_field('excerpt_image', <data url>)`. See [[web-ui]], [[webapi-bridge]].

**Failure handling — the blob must never persist.** `set_excerpt_img` saves *first* (the
data URL hits the file) and only *then* localizes, so a hook failure would otherwise
leave a 100KB+ base64 blob committed to the post. Because the hook can fail transiently
(node/sharp cold start, a momentary file lock), `_localize_excerpt_image` retries once
for a `data:` value and, if it still fails, **clears the image and re-saves** so the
markdown stays clean — better a missing preview image than a blob in git. A plain remote
http(s) URL that fails is left in place (small, still renders). This is an invariant —
see [[invariants-and-traps]].

### Rendering the saved image back (card preview)

Once self-hosted, `image:` is a site-absolute `/assets/posts/<slug>.header.webp`
that lives under the site's **`public/`** dir, not next to the posts folder.
`rendering.excerpt_image_local` resolves it by walking up to the site root
(`localize.find_repo_root`, the same anchor the hook uses) then into `public/`,
and embeds the file as a `data:` URL so the card `<img>` renders and html2canvas
can capture it untainted. MIME comes from `localize.file_to_data_url`, which fills
the webp/avif gap Windows' `mimetypes` lacks — an `<img>` won't render a
`data:application/octet-stream` payload. Remote/unresolved values pass through
untouched. (Earlier this resolved against `posts_folder.parent`, so post-migration
Astro images showed a broken-image icon.)

## See also
- [[serializers]] · [[jekyll-format]] · [[file-storage]] · [[bilingual-pairing]] · [[templates]]
