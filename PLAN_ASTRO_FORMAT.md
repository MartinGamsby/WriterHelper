# Plan: emit posts in the Astro format for martingamsby.com

Status: proposed (not started). Written 2026-06-12. Delete this file once
implemented and the Memory is updated — the Memory describes state, this
describes a change.

## Context

The two Jekyll blogs are being replaced by one bilingual Astro site
(`C:\Users\Martin\Documents\GitHub\martingamsby.com`, live at
https://martingamsby.github.io/martingamsby.com/ until the DNS cutover; see its
`PLAN.md` + `wiki/`). WriterHelper is the deterministic authoring pipeline
(model → template → `ContentFile.create_file`) and must write the new format.
The site repo briefly had a `new-post` script/skill — it gets deleted as part of
this work; WriterHelper is the one authoring tool.

## Target format (enforced by `src/content.config.ts` zod schema in the site repo)

```markdown
---
title: "Sample Title"
date: 2026-06-12
translationKey: 2026-06-12-sample-title
facets: [dev, ideas]
tags: [Gamsblurb]
draft: true
image: assets/img/foo.jpg
---

Body markdown — NO duplicated `### **<TITLE>**` heading (the site layout
renders the title).

---

- [X/Twitter](https://x.com/...)
```

- Folders: `<site>/src/content/blog/fr/` and `.../en/`.
- Filename `<YYYY-MM-DD>-<slug>.md`; the file stem IS the public URL slug:
  `/<lang>/blog/<stem>/`. Existing `get_slug()` output is compatible — reuse it.
- `facets`: `dev | physics | fiction | music | ideas` (0..n) — drives the site's
  "doors". Language-independent: one value per article *pair*.
- `translationKey`: replaces `ref:`. Same literal value in both languages' files;
  the site's language toggle resolves the twin through it.
- `draft: true` hides the post from the build; omitted when publishing.
- `image`: optional (needs a one-line schema addition site-side, see Companion).
- Footer links block: unchanged.

## Design decisions

1. **Serializer seam (the only structural change).** Extract the format-specific
   code (template fill + `change_article` parsing) behind a `PostSerializer`
   protocol: `serialize(model) -> str`, `parse(text) -> fields`, twin-reference
   semantics. Two implementations: `JekyllSerializer` (current behavior moved
   verbatim, golden-tested) and `AstroSerializer` (new). No behavior change for
   Jekyll output.
2. **Dual-write during the transition** *(recommended — decision A below)*.
   Every save writes Jekyll into the old repos (exactly as today) AND Astro into
   the site repo. The old blogs are still the URLs readers know; the new site
   doesn't have the back-catalog until Phase 2 migration lands. After migration +
   redirect stubs ship, Jekyll output is switched off in settings (no code change).
3. **`translationKey` is generated once and sticky.** At first save of a pair:
   `<date>-<slug(EN title)>` (matches the convention of the two posts already in
   the site repo). Stored on the model, round-tripped from disk, and NEVER
   regenerated on title/date change — the filename may change (URL changes are
   visible and deliberate), the pairing key must not.
4. **Twin lookup by key scan.** Loading an Astro file finds its twin by scanning
   the other language's folder for the same `translationKey` (a few hundred small
   files — trivial; cache the index per session). Replaces the `ref`-URL
   filename derivation. Jekyll loading keeps the `ref` recursion untouched.
5. **`categories` are dropped in Astro output** *(decision C)*. The
   `Length: Short` label is derivable from content; `Gamsblurb` survives as a
   tag. Jekyll output keeps categories unchanged.
6. **`excerpt_image` maps to `image:`** (omitted when empty).
7. **New shared pair-fields in the model + UI**: `facets` (5 checkboxes in
   `ArticleMeta.qml`; one shared value mirrored to both languages) and `draft`
   (shared checkbox). Setters emit `updated` like every other field.
8. **Share URLs for social posts** *(decision B)*: new `[URLs] astro_website` per
   language ini (e.g. `https://martingamsby.com/fr/blog/` post-cutover). Until
   the new site carries the back-catalog + redirects, X/Bluesky posts keep
   sharing the OLD Jekyll URL; flipping to the new URL later is an ini edit.
9. **Format auto-detection on load**: frontmatter with `layout: post` ⇒ Jekyll
   parser (incl. the `### **title**` strip); `translationKey:` ⇒ Astro parser.
   Old posts stay loadable forever.

## Implementation steps (follow this repo's Memory workflow)

1. `settings_<hl>.ini`: add `[Paths] astro_posts = <site>/src/content/blog/<hl>`
   and `[URLs] astro_website`; existing keys untouched.
2. `templates/post_astro.md` (new): the frontmatter above, `<CONTENT>`, footer —
   no body title heading.
3. `serializers.py` (new, < 350 lines): protocol + the two implementations;
   move existing fill/parse logic into `JekyllSerializer` without behavior change.
4. `article.py` / `model.py`: `translation_key`, `facets`, `draft` fields;
   sticky-key logic; pair-shared propagation (like `date` today).
5. `filemanager.py` / `on_updated`: write through every *enabled* serializer
   (enabled = its path key present in settings); write-new/delete-old rename
   semantics applied per target folder.
6. `change_article`: detect format, route to the right parser; Astro twin
   resolution via key scan; `delete_last=False` guarantees unchanged.
7. Tests (deterministic, pytest): golden-file serialize for both formats;
   parse(serialize(x)) round-trip; sticky key under title+date change; twin
   scan; dual-write produces 4 files with consistent keys; legacy Jekyll file
   load unchanged.
8. Update Memory: `file-storage/` (astro format page + summary), `model/`
   (article/articles, translation), `templates/summary.md`, `terminology.md`
   (facet, translationKey, door).

## Companion changes (martingamsby.com repo)

- `src/content.config.ts`: add `image: z.string().optional()`.
- The `new-post` **skill** was removed (authoring is deterministic, not a skill);
  the `tools/new-post.mjs` **script stays** as a low-level helper this pipeline (or
  a human) can call. CLAUDE.md/README name WriterHelper as the authoring tool.
- Wiki: `sources/writerhelper.md` page + log entry (done 2026-06-12).

## Bigger picture: maybe integrate INTO martingamsby.com instead (deferred)

Martin's alternative to keeping WriterHelper a separate Qt app that writes files:
**fold it into the martingamsby.com site as a web app.** He already attempted a
web conversion once — this repo has a started `web/` folder and `webapi.py`. He
thinks the Astro site is a stronger base for a second attempt and that it could
be done better now.

If we go this route, the "serializer seam" work above still applies (the format
contract is the same), but the *host* changes: instead of the Qt model emitting
into two folders, an Astro/endpoint UI on the site would create/translate/post.
Decide reuse of the existing `webapi.py` vs a fresh Astro-native authoring UI.

**Explicitly not this session** (Martin: "it's too long already"). Capture intent;
implement later. This choice (separate-app dual-format vs web-integrated) should be
settled BEFORE building the serializers, since it changes where they live.

## Decisions Martin must confirm

- **A. Dual-write vs hard switch** — recommend dual-write until Phase 2
  migration + redirects are live.
- **B. Social posts share which URL during the transition** — recommend the old
  Jekyll URL until redirects exist, then flip the ini.
- **C. Drop `categories` from Astro frontmatter** — recommend yes.
