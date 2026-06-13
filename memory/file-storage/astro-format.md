# Astro Post Format

The **written** format. WriterHelper now emits posts for the bilingual Astro site
`martingamsby.com` (`src/content/blog/<hl>/`). Jekyll is load-only legacy — see
[jekyll-format.md](jekyll-format.md). Hard switch (no dual-write): saving writes
Astro only.

Serializer: `serializers.py`. Reference layout: `templates/post_astro.md` (the
optional `draft`/`image` lines and the footer block are conditional, so
`serializers.serialize` builds the string in code rather than string-replacing the
template).

## Anatomy

```markdown
---
title: "Sample Title"
date: 2026-06-13
translationKey: 2026-06-13-sample-title
facets: [dev, ideas]
tags: [Gamsblurb]
draft: true
image: assets/img/foo.jpg
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
| `translationKey` | `get_translation_key()` | sticky pairing key; see below |
| `facets` | `facets` | bare flow list `[dev, ideas]`; `[]` when empty |
| `tags` | `get_tags()` | bare `[Gamsblurb,Vie]` (raw comma string) |
| `draft` | `draft` | emitted as `draft: true` ONLY when True; omitted to publish |
| `image` | `excerpt_image` | emitted only when non-empty (maps to Jekyll `excerpt_image`) |
| body | `content` | no title heading |
| footer | `footer_md()` | `- [text](url)` lines; whole `---` + footer block omitted when no links |

`categories` is intentionally dropped (the length label is derivable; `Gamsblurb`
survives as a tag).

## translationKey (sticky pairing key)

Replaces Jekyll's `ref:`. Same literal value in both languages' files; the site's
language toggle resolves the twin through it.

- Generated once as `<date>-<EN-slug>` (the English title drives it, matching the
  back-catalog convention). Both FR and EN derive the same value.
- **Frozen** after first generation (`ArticleModel.translation_key`): later title
  or date edits move the filename/URL but never the key. Round-tripped from disk on
  load; cleared by `new_article` (a fresh post gets a fresh key).
- Freeze only happens once a real EN slug exists; while EN is untitled the key is
  computed transiently from the current language's own slug.

## Filename & URL

`<YYYY-MM-DD>-<slug>.md`; the file **stem is the public URL slug**:
`/<lang>/blog/<stem>/`. `get_slug()` output is reused unchanged (still drives the
filename). Public URL via `get_post_url()` = `<website><date>-<slug>/`, where
`[URLs] website` is the Astro base (`https://martingamsby.com/<hl>/blog/`). Social
posts and the "Based on" link share this Astro URL (transition decision B: new URL
now).

## Load: format auto-detection (`serializers.parse`)

`parse(article, text, old_date, change_ref)` parses the frontmatter, then routes:
- `layout: post` (or a `ref:` key) ⇒ Jekyll parser (strips `### **title**`,
  ref-URL twin derivation). Old posts stay loadable forever.
- otherwise ⇒ Astro parser.

Astro body/footer split takes the footer as whatever follows the **last** `\n---\n`,
so a markdown horizontal rule inside the body is not mistaken for the footer.

`delete_last` is forced False during load and restored after; the model is re-saved
in Astro format at the end (same contract as the old `change_article`).

## Astro twin resolution

`_resolve_astro_twin`: scan the other language's folder for a file whose frontmatter
has the same `translationKey:` line, then load it into `ref` (`change_ref=False`).
If none found, `ref.new_article()`. Replaces Jekyll's ref-URL filename derivation.

## See also
- [jekyll-format.md](jekyll-format.md) — legacy, load-only
- [summary.md](summary.md)
- [../model/article-model.md](../model/article-model.md)
- [../templates/summary.md](../templates/summary.md)
