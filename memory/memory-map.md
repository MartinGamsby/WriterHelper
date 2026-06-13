# Memory Map

Index of all Memory files. Read this first when seeding a session.

## Top level
- [summary.md](summary.md) — one-paragraph project snapshot + module diagram
- [terminology.md](terminology.md) — domain terms
- [practices.md](practices.md) — invariants, traps, dos/don'ts
- `tmp/` — git-ignored scratch dir for session-only notes

## Domains
- **model/** — Qt-free data + rendering layer (`article.py`, `rendering.py`, `articles.py`)
  - [model/summary.md](model/summary.md)
  - [model/article-model.md](model/article-model.md) — fields, setters, lifecycle, change_article parser
  - [model/articles-model.md](model/articles-model.md) — FR/EN pairing via `set_ref`
  - [model/translation.md](model/translation.md) — Google Translator src→empty-dst
  - [model/rendering.md](model/rendering.md) — the five `content_md_*` flavors (now in `rendering.py`)
  - [model/post-routing.md](model/post-routing.md) — text-vs-image decision (now `publishing.prepare_post`)
  - [model/links.md](model/links.md) — named link slots, footer
- **web-ui/** — pywebview frontend (the current UI)
  - [web-ui/summary.md](web-ui/summary.md) — bridge + JS module map
  - [web-ui/bridge.md](web-ui/bridge.md) — `webapi.Api` methods, pull-based refresh
  - [web-ui/frontend.md](web-ui/frontend.md) — columns, editors, debounced save
  - [web-ui/capture.md](web-ui/capture.md) — html2canvas pagination + sizing helpers
- **posting/** — social platform adapters + publish flow
  - [posting/summary.md](posting/summary.md)
  - [posting/popup-flow.md](posting/popup-flow.md) — `publishing.py` prepare/publish + confirmation popup
  - [posting/post-base.md](posting/post-base.md) — `Post` base, `[Access]` INI shape
  - [posting/bluesky.md](posting/bluesky.md) — atproto.Client
  - [posting/x.md](posting/x.md) — tweepy v1+v2
  - [posting/facebook.md](posting/facebook.md) — Graph v18, NOT inheriting Post
  - [posting/linkedin.md](posting/linkedin.md) — BROKEN, do not import
- **file-storage/** — disk layout
  - [file-storage/summary.md](file-storage/summary.md)
  - [file-storage/jekyll-format.md](file-storage/jekyll-format.md) — frontmatter, slug rules, save-on-update
- **templates/** — markdown placeholders
  - [templates/summary.md](templates/summary.md) — the four files + placeholder vocabulary
- **ui/** — LEGACY QML tree (used only by `writerhelper_qt.py`)
  - [ui/summary.md](ui/summary.md) — marked legacy; supersedes by web-ui/
  - [ui/qml-tree.md](ui/qml-tree.md), [ui/image-capture.md](ui/image-capture.md), [ui/checklist.md](ui/checklist.md)
