# serializers.py — the format seam

The single place that knows the on-disk `.md` format. `serialize(article)` writes the
[[astro-format]] file; `parse(article, text, old_date, change_ref)` reads a file back,
auto-detecting Jekyll vs Astro. Saving is **Astro only** (hard switch);
[[jekyll-format]] is load-only.

## serialize(article) → str

Builds the Astro string in code (not by string-replacing a template) because the
optional `draft`/`image`/`imageThumb` lines and the footer block are conditional.
`templates/post_astro.md` is a reference layout only. Also exposes `FACETS` (the five
[[glossary]] facet values, kept in lock-step with the site's `content.config.ts` enum).

The `title:` line goes through `_yaml_dq` (escape `\` then `"`) so a title containing
double quotes stays inside its double-quoted scalar instead of closing it early and
producing un-parseable YAML. This is round-trip-critical: without it, loading a quoted
title and re-saving (every save does) silently corrupted the file. Other frontmatter
fields are controlled vocabularies or slugs and need no escaping.

## parse(...) — load + route

1. Parse the frontmatter.
2. Route: `layout: post` (or a `ref:` key) ⇒ Jekyll parser (`_load_jekyll`, moved
   verbatim from the old `change_article`); otherwise ⇒ Astro parser.
3. Resolve the twin (`change_ref=False` guards recursion).
4. `delete_last` forced False during load, restored after; the model is re-saved in
   Astro format at the end.

Astro body/footer split takes the footer as whatever follows the **last** `\n---\n`, so
a markdown horizontal rule inside the body isn't mistaken for the footer.

## Twin resolution (Astro)

`_resolve_astro_twin` → `_find_twin_file(folder, key)`:
- **O(1) fast path**: a file named `<key>.md` IS the twin (the back-catalog convention
  is `translationKey` == EN stem).
- **Fallback scan**: only when filename ≠ key — read each post's YAML **header** only
  (`_header_has_key` stops at the closing `---`), never the body. (Replaced a
  full-file scan that caused a multi-second startup freeze.)
- **Self-heal**: if the loaded twin's key ≠ the lookup key, rewrite + re-save the ref's
  key to re-link drifted/"swapped" legacy pairs.

Full design rationale: [[bilingual-pairing]].

## Image self-hosting hook

After an Astro save, a remote `excerpt_image` is localized via `localize.py` — see the
detailed treatment in [[astro-format]].

## See also
- [[astro-format]] · [[jekyll-format]] · [[file-storage]] · [[bilingual-pairing]]
