# File Storage — Summary

Where article content lives on disk and how it's named.

## Two locations, one per language

Configured in `settings_<hl>.ini` under `[Paths]:Posts`. Current values on the dev machine:
- FR → `C:\Users\Martin\Documents\GitHub\martingamsby.github.io\_posts`
- EN → `C:\Users\Martin\Documents\GitHub\martingamsby.gitbub.io_en\_posts` (note the typo — see [../practices.md](../practices.md))

Both folders are part of separate Jekyll-site git repos checked out alongside this project. WriterHelper writes `.md` files into them; the operator commits and pushes them manually.

## Naming

`<YYYY-MM-DD>-<slug>.md` (Jekyll's standard `_posts` convention).
- Date comes from `ArticleModel.date` (defaults to today, can be overridden via "Date override" checkbox in the UI).
- Slug comes from `ArticleModel.get_slug()`: `unidecode(title)` → lowercase → `-`-collapsed → non-alphanumeric stripped.

## Save semantics

Every property setter that detects a real change emits `updated`, which triggers `on_updated` → `ContentFile.create_file(folder, slug, content_md, delete_last, date)`.

The persistence layer (`filemanager.py`):
- Writes `<folder>/<date>-<slug>.md` with the current `content_md` (full Jekyll, frontmatter + body + footer).
- If `delete_last` is True and the previous filename differs and still exists, deletes it. This is how a title or date change *renames* the file: write new, delete old.

A `threading.Lock` guards the write. `delete_last` is forced False around `change_article`, `new_article`, and `new_both_articles` so loading or transitioning never deletes a real file.

## Files in this folder
- [jekyll-format.md](jekyll-format.md) — frontmatter shape, what each field means, the round-trip with `change_article`

## See also
- [../model/article-model.md](../model/article-model.md) — the `on_updated` lifecycle
- [../templates/summary.md](../templates/summary.md) — `templates/post.md` is what gets written
