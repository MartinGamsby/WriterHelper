# Log

Append-only timeline. One line per operation: `## [YYYY-MM-DD] operation | description`.
Grep-able. The wiki *pages* hold current state; this file holds the sequence of how it
got there.

## [2026-06-14] ingest | Drop/Browse a local image for an article ([[astro-format]], [[web-ui]], [[webapi-bridge]]): meta panel gains a drop zone + Browse… button. Both convert the file to a `data:` URL and feed `set_excerpt_img`, reusing the existing self-hosting hook unchanged (data: was already first-class in `is_remote`/`isExternal`/Node fetch) → slug-named webp pair. New: `localize.file_to_data_url`, `webapi.open_image`, `Meta.wireImage`, app.js stray-drop guard. No change to the sibling site repo.

## [2026-06-14] fix | Card image-preview broken after the Astro migration ([[astro-format]]): `rendering.excerpt_image_local` resolved `/assets/posts/<slug>.header.webp` against `posts_folder.parent` (= `…/blog`) but the webp lives under the site's `public/`. Now walks up to the site root via `localize.find_repo_root` (renamed from `_find_repo_root`) then into `public/`, with absolute + legacy-blog-relative fallbacks. Also consolidated `rendering.data_url` onto `localize.file_to_data_url` so webp gets a real `image/webp` MIME (Windows mimetypes lacks it; `<img>` won't render `application/octet-stream`).

## [2026-06-13] migrate | Converted the old `memory/` Memory system to the Karpathy-style `wiki/`. Ported every memory file (incl. the `startup-freeze` + `translationkey-bug` additions) into [[overview]], [[glossary]], concepts/, architecture/, sources/; rewrote `CLAUDE.md` to point at the wiki; added the `llm-wiki` skill (`.claude/skills/llm-wiki/`); repointed `.gitignore` (`wiki/tmp/`). No code behavior changed.

## [2026-06-13] ingest | Domain cutover for [[martingamsby-site]]: site live at apex `martingamsby.com`; WriterHelper's social/"Based on" URLs share the Astro base `https://martingamsby.com/<hl>/blog/`.

## [earlier] ingest | Hard switch to the Astro write format ([[astro-format]]): `serializers.py` became the format seam; `settings_<hl>.ini` repointed at `martingamsby.com/src/content/blog/<hl>`; Jekyll became load-only ([[jekyll-format]]).

## [earlier] ingest | Self-hosted preview images: remote `excerpt_image` URLs are downloaded + re-encoded to webp by the site's `tools/localize-images.mjs`, invoked via [[serializers]]'s `localize.py` hook. Frontmatter gains `image:` + `imageThumb:`.

## [earlier] refactor | Split the monolithic `model.py` into the Qt-free [[model-layer]] ([[article-model]], [[articles-model]], [[rendering-module]], [[publishing]]); built the pywebview [[web-ui]]. `model.py` + `backend.py` are now legacy ([[legacy-qt-ui]]).

## [earlier] ingest | Publishing became two-phase behind a confirmation popup ([[social-publishing]]): `prepare_post` (no side effects) + `publish`.

## [earlier] security | LinkedIn credentials that had been duplicated into a memory file were scrubbed from git history; `post_linkedin.py` values redacted in the working tree. The adapter stays broken/unused. See [[linkedin-adapter]], [[secrets]].
