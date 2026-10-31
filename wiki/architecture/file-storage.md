# File storage

Where article content lives on disk and how it's named/written. The persistence
mechanics are in `filemanager.py` (`ContentFile`); the format is [[serializers]].

## Two locations, one per language

Configured in `settings_<hl>.ini` under `[Paths] Posts`. On the dev machine both point
inside the single bilingual Astro repo [[martingamsby-site]]:
- FR → `…\martingamsby.com\src\content\blog\fr`
- EN → `…\martingamsby.com\src\content\blog\en`

WriterHelper writes `.md` files into them; the operator commits + pushes by hand. The
format written is [[astro-format]]; the old Jekyll repos are no longer written (hard
switch — flipping back would just be an INI edit). `settings*.ini` is git-ignored
(user-private, see [[secrets]]). Legacy Jekyll posts remain loadable via format
auto-detection.

## Naming

`<YYYY-MM-DD>-<slug>.md`. Date from `ArticleModel.date` (today by default, overridable
via the "Date override" checkbox); slug from `get_slug()`.

## Save semantics

Every real-change setter calls `updated()` → `ContentFile.create_file(folder, slug,
content_md, delete_last, date)`:
- Writes `<folder>/<date>-<slug>.md` with the current Astro `content_md`.
- If `delete_last` and the previous filename differs and still exists, deletes it — this
  is how a title/date change **renames** (write new, delete old).
- A `threading.Lock` guards the write. `delete_last` is forced False around
  `change_article`, `new_article`, `new_both_articles`.
- `updated()` skips the write when `get_slug()` is empty (no stray `<date>-.md`).

See [[auto-save-and-pull-ui]] for the lifecycle.

## See also
- [[serializers]] · [[astro-format]] · [[jekyll-format]] · [[article-model]] · [[martingamsby-site]]
