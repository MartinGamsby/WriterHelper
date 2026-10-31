# Index

Catalog of the WriterHelper wiki. Read this first to locate pages; don't bulk-load. Link
between pages with `[[page-name]]` (filename without `.md`/path). Schema + workflows:
`.claude/skills/llm-wiki/SKILL.md`.

## Top level
- [[overview]] — the whole system in one screen + the architecture diagram
- [[glossary]] — domain terms, one line each
- [[log]] — append-only timeline of operations

## Concepts (cross-cutting design)
- [[bilingual-pairing]] — FR↔EN twins: `ref` coupling, the sticky `translationKey` stamped on both, O(1) twin resolution + self-heal
- [[machine-translation]] — one-way Google translate that fills only an empty twin
- [[auto-save-and-pull-ui]] — save-on-every-edit, rename-by-delete, the pull-based UI
- [[content-flavors]] — the five render shapes of one article
- [[social-publishing]] — two-phase publish behind a confirmation popup; text · thread · image modes; api vs browser transport
- [[browser-hook]] — posting via Claude in Chrome: `browser_jobs/` queue, `/chrome-post` skill, pulled results, `settings_publish.ini` (transports, hidden, hook, accounts)
- [[link-slots]] — named `(text,url)` link slots, the file footer, the publish guard
- [[image-card-capture]] — html2canvas branded-JPEG generation (slug-named) + sizing
- [[video-posts]] — PLANNED: short vertical videos (TikTok video, YouTube Shorts) from the card, posted via the browser hook; PoC = text fading in from black
- [[invariants-and-traps]] — the non-negotiables, the landmines, tests, style
- [[secrets]] — where credentials live; the LinkedIn scrub; the wiki rule
- [[tag-vocabulary]] — controlled bilingual tags: `tag_vocab.py` vocabulary, FR↔EN pairing in `set_tags`, the facet-aware picker (`tag_index.py`), and the `migrate_tags.py` normalizer
## Architecture (the code map)
- [[model-layer]] — the Qt-free split overview (`article`/`rendering`/`articles`/`publishing`/`serializers`)
- [[article-model]] — `article.py`: state, setters, `updated()`, pairing, navigation, slug
- [[articles-model]] — `articles.py`: the FR/EN pairing factory + `translate`
- [[rendering-module]] — `rendering.py`: the HTML flavor functions
- [[serializers]] — `serializers.py`: the format seam (serialize/parse, twin lookup)
- [[astro-format]] — the written format: frontmatter, `translationKey`, image self-hosting
- [[jekyll-format]] — legacy, load-only
- [[file-storage]] — disk layout, naming, `ContentFile` save semantics
- [[templates]] — the markdown templates + placeholder vocabulary
- [[web-ui]] — `web/`: layout, JS modules, the two columns
- [[webapi-bridge]] — `webapi.Api`: methods, `get_state` shape, the no-public-attrs invariant
- [[publishing]] — `platforms.py` registry (transports) + `publishing.py` prepare/publish/`_plan` + `instagram_flow.py`
- [[thread-split]] — `thread_split.py`: pure long-article → editable thread splitter
- [[post-base]] — `post.py`: the adapter base class + override contract
- [[bluesky-adapter]] — `post_bsky.PostBsky` (atproto); clickable link facets + optional external link-preview card (`fetch_external_card`, YouTube-aware)
- [[x-adapter]] — `post_x.PostX` (tweepy v1+v2); optional (`x = api`), default is the browser hook
- [[facebook-adapter]] — `post_fb.PostFB` (Graph API **Page** posts); optional (`facebook = api`), default is the browser hook (personal profile); includes the non-expiring Page-token steps
- [[instagram-adapter]] — `post_ig.PostIG` (Graph API, reuses the FB token + `IgUserId`); optional (`instagram = api`): image-only, IG-must-be-last, two-step auto-push of the JPEG to a public GitHub-raw URL (`site_push.py`)
- [[legacy-qt-ui]] — the superseded PySide6/QML stack (do not run now)

## Sources (external properties)
- [[martingamsby-site]] — the Astro site WriterHelper authors for; the doors/facets/twin contract + the image-localize hook
