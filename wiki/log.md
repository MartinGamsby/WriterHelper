# Log

Append-only timeline. One line per operation: `## [YYYY-MM-DD] operation | description`.
Grep-able. The wiki *pages* hold current state; this file holds the sequence of how it
got there.

## [2026-06-13] migrate | Converted the old `memory/` Memory system to the Karpathy-style `wiki/`. Ported every memory file (incl. the `startup-freeze` + `translationkey-bug` additions) into [[overview]], [[glossary]], concepts/, architecture/, sources/; rewrote `CLAUDE.md` to point at the wiki; added the `llm-wiki` skill (`.claude/skills/llm-wiki/`); repointed `.gitignore` (`wiki/tmp/`). No code behavior changed.

## [2026-06-13] ingest | Domain cutover for [[martingamsby-site]]: site live at apex `martingamsby.com`; WriterHelper's social/"Based on" URLs share the Astro base `https://martingamsby.com/<hl>/blog/`.

## [earlier] ingest | Hard switch to the Astro write format ([[astro-format]]): `serializers.py` became the format seam; `settings_<hl>.ini` repointed at `martingamsby.com/src/content/blog/<hl>`; Jekyll became load-only ([[jekyll-format]]).

## [earlier] ingest | Self-hosted preview images: remote `excerpt_image` URLs are downloaded + re-encoded to webp by the site's `tools/localize-images.mjs`, invoked via [[serializers]]'s `localize.py` hook. Frontmatter gains `image:` + `imageThumb:`.

## [earlier] refactor | Split the monolithic `model.py` into the Qt-free [[model-layer]] ([[article-model]], [[articles-model]], [[rendering-module]], [[publishing]]); built the pywebview [[web-ui]]. `model.py` + `backend.py` are now legacy ([[legacy-qt-ui]]).

## [earlier] ingest | Publishing became two-phase behind a confirmation popup ([[social-publishing]]): `prepare_post` (no side effects) + `publish`.

## [earlier] security | LinkedIn credentials that had been duplicated into a memory file were scrubbed from git history; `post_linkedin.py` values redacted in the working tree. The adapter stays broken/unused. See [[linkedin-adapter]], [[secrets]].
