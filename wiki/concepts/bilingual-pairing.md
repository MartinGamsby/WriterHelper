# Bilingual pairing (FR ↔ EN twins)

The defining concept: every post exists as a French + English **pair** kept in lockstep.
Two `ArticleModel` instances live for the whole session — one `hl="fr"`, one `hl="en"` —
mutually coupled, and the on-disk files pair through a shared key.

## In-memory coupling: `ref`

`ArticleModel.set_ref(other)` stores `self.ref = other`. [[articles-model]]'s
`create(config_dir)` factory wires it both ways. `ref` drives twin loading and lets each
side read the other's slug/URL.

Pair-shared fields mirror onto `ref` and save both sides:
- `set_facets(list)` — the `facets` ([[glossary]] door tags) cleaned + mirrored.
- `set_draft(bool)` — the `draft` flag mirrored.
- `date` — mirrored (twins share a date).

## On-disk pairing: `translationKey` (sticky, stamped on both)

Replaces Jekyll's `ref:` URL. The **identical literal value** in both languages'
frontmatter; the site's language toggle resolves the twin through it. The value is
arbitrary — only *matching* matters. `get_translation_key()` resolves in order:

1. this side already has a key → return it (frozen);
2. the **ref** has a key → adopt it (so re-translating one side via `new_article`
   re-links instead of forking);
3. neither → mint `<date>-<EN-slug>` (falls back to the current language's slug while
   EN is untitled) and **stamp it onto BOTH `self` and `ref`** in memory.

Because the mint writes the key onto both models, the two files **cannot diverge** by
authoring order: whichever side first needs a key mints it for the pair; the other
adopts it on its next save. (The earlier design froze each side independently, so
authoring FR before EN left FR keyed `<date>-<fr-slug>` and EN `<date>-<en-slug>` →
unlinked.) The getter never touches disk; the shared key reaches the twin's file
through the normal save flow. Cleared by `new_article`, but re-adopted via rule 2 if
the pair still has one.

Code: `get_translation_key()` in [[article-model]]; written/read by [[serializers]]
per [[astro-format]].

## Twin resolution on load

When you open one side, the other is auto-loaded. Routed in [[serializers]]
(`_resolve_astro_twin` → `_find_twin_file`):

- **Astro fast path (O(1)):** the back-catalog convention is `translationKey` == the
  EN file's stem, so a file literally named `<key>.md` IS the twin — returned without
  re-reading. (Loading the most-recent FR post at startup hits this.)
- **Astro fallback scan:** only when filename ≠ key (renamed after the key froze, or an
  FR-derived key) — read just each post's YAML **header** (stop at the closing `---`),
  never the body. This replaced a full-file scan of every sibling that caused a
  multi-second "startup freeze".
- **Self-heal:** if the loaded twin's key ≠ the lookup key (legacy "swapped" data where
  FR/EN were keyed to each other's slug), rewrite the ref's key and re-save — re-linking
  both files on disk. No-op once they agree.
- **Jekyll (legacy load):** strip `ref.website_url` from the frontmatter `ref:` URL to
  get the slug, prepend `<date>-`, find that file in `ref.posts_folder`.

The `change_ref=False` guard prevents infinite mutual recursion.

## See also
- [[article-model]] — `get_translation_key`, `get_ref`, `new_*` navigation
- [[articles-model]] — the pairing factory + `translate`
- [[astro-format]] — how the key is written/read
- [[machine-translation]] — filling the empty twin from its sibling
