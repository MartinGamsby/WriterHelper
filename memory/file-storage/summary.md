# File Storage — Summary

Where article content lives on disk and how it's named.

## Two locations, one per language

Configured in `settings_<hl>.ini` under `[Paths]:Posts`. Current values on the dev machine:
- FR → `C:\Users\Martin\Documents\GitHub\martingamsby.com\src\content\blog\fr`
- EN → `C:\Users\Martin\Documents\GitHub\martingamsby.com\src\content\blog\en`

Both folders are inside the single bilingual **Astro** site repo (`martingamsby.com`)
checked out alongside this project. WriterHelper writes `.md` files into them; the
operator commits and pushes manually. The format written is **Astro** (see
[astro-format.md](astro-format.md)); the old Jekyll repos are no longer written
(hard switch — `settings_<hl>.ini` was repointed; flipping back would just be an ini
edit). `settings*.ini` is git-ignored (user-private). Legacy Jekyll posts remain
loadable via format auto-detection.

## Naming

`<YYYY-MM-DD>-<slug>.md` (Jekyll's standard `_posts` convention).
- Date comes from `ArticleModel.date` (defaults to today, can be overridden via "Date override" checkbox in the UI).
- Slug comes from `ArticleModel.get_slug()`: `unidecode(title)` → lowercase → `-`-collapsed → non-alphanumeric stripped.

## Save semantics

Every property setter that detects a real change emits `updated`, which triggers `on_updated` → `ContentFile.create_file(folder, slug, content_md, delete_last, date)`.

The persistence layer (`filemanager.py`):
- Writes `<folder>/<date>-<slug>.md` with the current `content_md` (now Astro:
  frontmatter + body + footer — `serializers.serialize`).
- If `delete_last` is True and the previous filename differs and still exists, deletes it. This is how a title or date change *renames* the file: write new, delete old.

A `threading.Lock` guards the write. `delete_last` is forced False around `change_article`, `new_article`, and `new_both_articles` so loading or transitioning never deletes a real file.

## Files in this folder
- [astro-format.md](astro-format.md) — the written format: frontmatter, translationKey, twin scan, format auto-detection
- [jekyll-format.md](jekyll-format.md) — legacy, load-only

## See also
- [../model/article-model.md](../model/article-model.md) — the `updated()` lifecycle
- [../templates/summary.md](../templates/summary.md) — `templates/post_astro.md` is the written layout
