# Memory Map

Index of all Memory files. Read this first when seeding a session.

## Top level
- [summary.md](summary.md) — one-paragraph project snapshot + module diagram
- [terminology.md](terminology.md) — domain terms
- [practices.md](practices.md) — invariants, traps, dos/don'ts
- `tmp/` — git-ignored scratch dir for session-only notes

## Domains
- **model/** — `model.py` data, rendering, translation, post routing
  - [model/summary.md](model/summary.md)
  - [model/article-model.md](model/article-model.md) — props, signals, slots, lifecycle, change_article parser
  - [model/articles-model.md](model/articles-model.md) — FR/EN pairing via `set_ref`
  - [model/translation.md](model/translation.md) — Google Translator src→empty-dst
  - [model/rendering.md](model/rendering.md) — the five `content_md_*` flavors
  - [model/post-routing.md](model/post-routing.md) — text-vs-image fallback, length thresholds
  - [model/links.md](model/links.md) — named link slots, footer
- **ui/** — QML tree
  - [ui/summary.md](ui/summary.md)
  - [ui/qml-tree.md](ui/qml-tree.md) — main + components, what each binds
  - [ui/image-capture.md](ui/image-capture.md) — `grabToImage` callback chain, sizes, naming
  - [ui/checklist.md](ui/checklist.md) — manual workflow encoded in `CheckList.qml`
- **file-storage/** — disk layout
  - [file-storage/summary.md](file-storage/summary.md)
  - [file-storage/jekyll-format.md](file-storage/jekyll-format.md) — frontmatter, slug rules, save-on-update
- **posting/** — social platform adapters
  - [posting/summary.md](posting/summary.md)
  - [posting/post-base.md](posting/post-base.md) — `Post` base, `[Access]` INI shape
  - [posting/bluesky.md](posting/bluesky.md) — atproto.Client
  - [posting/x.md](posting/x.md) — tweepy v1+v2
  - [posting/facebook.md](posting/facebook.md) — Graph v18, NOT inheriting Post
  - [posting/linkedin.md](posting/linkedin.md) — BROKEN, do not import
- **templates/** — markdown placeholders
  - [templates/summary.md](templates/summary.md) — the four files + placeholder vocabulary
