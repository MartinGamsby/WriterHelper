# Tag vocabulary, pairing, picker & migration

The controlled bilingual tag system. Where [[glossary]] **facets** are a closed enum of
five language-independent topics, **tags** are a richer, curated vocabulary of reused
labels that DO differ by language (`Health`↔`Santé`) and now stay matched across the
FR/EN twin. This page covers the four pieces: the vocabulary, pairing, the authoring
picker, and the one-shot normalization migration.

## The problem it fixes

Tags were free-text, per-language, per-article, seeded only with `Gamsblurb`
(`DEFAULT_TAGS`). The back-catalog showed the damage: casing dups (`Personal
Development`/`Personal development`), typos (`Heatlh`, `Gamsblur`, `Allimentation`),
synonyms (`Learn`/`Learning`), cross-language leaks (`Astrophysique` in EN files,
`Purpose` in FR), and FR/EN twins carrying *different* tag sets (`translate()`
Google-translated tags, so `Learn`→`Apprendre` not `Apprentissage`).

## 1. The vocabulary — `tag_vocab.py`

A `_CONCEPTS` table of `(en, fr, [aliases])`. A *concept* is one reusable tag; `en==fr`
for language-neutral ones (proper nouns, `Gamsblurb`, `Ikigai`, `C++`). The concept **id
is its English label**. Lookups are `casefold()`+whitespace-normalized, so every casing
variant collapses for free — aliases only cover what casefolding can't: typos, synonyms,
and merged-word accidents (`GamsblogGamsblurb`). Because BOTH labels key the concept, a
leaked tag resolves and re-renders in the file's own language.

Key helpers: `normalize(label)→concept|None`, `concept_id(label)`,
`label(id, hl)`, `canonical_label(raw, hl)` (folds a raw label to its `hl` label;
unknown tags pass through trimmed), `concepts_in(tag_string)`, `split`/`join`
(tags are stored as one comma-separated string). `HOUSE_TAG = "Gamsblurb"`.

## 2. Pairing — `set_tags` mirrors the twin

[[article-model]]'s `set_tags` now mirrors *vocabulary* tags onto the ref, like
`set_facets` mirrors facets ([[bilingual-pairing]]). `_mirror_tags_to_ref` ensures every
concept on the edited side exists — in the twin's own language — on the ref, while
leaving the twin's non-vocabulary one-offs alone. The edited side is authoritative for
the shared concept set; the twin's existing order is preserved (minimal churn), and it
writes the ref directly (not via `set_tags`) so the two can't mirror forever.
[[articles-model]]'s `translate` now maps known concepts through the vocab
(deterministic) and only Google-translates genuine one-offs.

## 3. The picker — suggestions in the web UI

`tag_index.py` scans the posts folder into `{freq, by_facet}` (cached, invalidated by a
file-count+mtime signature). Two deterministic signals, exposed by
[[webapi-bridge]]'s `tag_suggestions(hl)`:
- **matching** — vocabulary ranked by co-occurrence with THIS article's facets on other
  posts (the "from the checked facets" idea);
- **popular** — overall frequency fallback, disjoint from matching; both exclude tags
  already applied and the house tag.

`toggle_tag(hl, label)` adds/removes a tag (idempotent per concept) via `set_tags`, so
pairing follows. The UI ([[web-ui]] `meta.js`) renders the two rows as clickable chips
under the Tags input; a click refreshes BOTH columns.

## 4. The migration — `migrate_tags.py`

One-shot normalizer over the site's `{fr,en}` post folders ([[martingamsby-site]]). Per
translationKey twin it: folds each raw tag to its `hl` vocabulary label; unions the
*vocabulary* concepts across the pair so both languages match (one-offs stay per-side);
guarantees `Gamsblurb` present once and **last** — **except quote posts** (any twin
tagged `Quote`/`Citation`), which carry NO house tag (`HOUSE_EXCLUSIVE = {"Quote"}`): a
quote isn't a Gamsblurb, and in the clean back-catalog the quote posts were the only ones
ever missing it. **Guidepour posts** (the `Djosh Sho` column): the `Fiction` tag is
never pair-unioned across the twin — some entries are real-life facts, so Fiction stays
exactly as authored on each side (a one-off removed it from the 8 real-life-fact pairs;
the column is defined by the `Djosh Sho` tag, not Fiction). It rewrites ONLY the `tags:` frontmatter line — every other byte is
preserved (the site migration kept bodies byte-for-byte). **Dry-run by default**;
`--write` applies. Pure planning (`plan_pair`, `replace_tags_line`) is unit-tested.

Dry-run on the real site (2026-06-17): **85 of 263 files** would change. **Not yet
applied** — the site repo had unrelated uncommitted work (the `aliases:` feature, plus
16 hand-edited tag lines), so the apply was left to the operator to run on a clean
branch and review via `git diff`.

## Code map

`tag_vocab.py` (table + lookups) · `tag_index.py` (frequency/co-occurrence index) ·
`migrate_tags.py` (normalizer) · `article.py` `set_tags`/`_mirror_tags_to_ref` ·
`articles.py` `_translate_tags` · `webapi.py` `tag_suggestions`/`toggle_tag` ·
`web/js/meta.js` `renderTagSuggestions`. Tests: `test_tag_vocab.py`,
`test_tag_index.py`, `test_webapi_tags.py`, `test_migrate_tags.py`, plus pairing tests
in `test_article.py`.

The site consumes the cleaned tags in two **constellations** (in the
`martingamsby.com` repo's wiki: `related-constellation`, `tag-galaxy`): a per-post
related-posts map (shared tags + facet, sized by popularity) and a `/[lang]/tags`
galaxy (tags as stars sized by frequency, coloured by dominant facet).

## See also
- [[bilingual-pairing]] — the FR↔EN coupling tags now join · [[article-model]] ·
  [[articles-model]] · [[webapi-bridge]] · [[serializers]] · [[martingamsby-site]]
