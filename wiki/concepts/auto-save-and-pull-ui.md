# Auto-save & the pull-based UI

Two coupled invariants define how state moves through WriterHelper: **every edit saves
immediately**, and **the UI re-reads state instead of being pushed to**.

## Auto-save (no save button)

Every `set_*` setter on [[article-model]] follows:

```python
if self.x != value:
    self.x = value
    self.updated()
```

`updated()` is a plain method (not a Qt signal anymore) that re-writes the `.md` via
`ContentFile.create_file(folder, slug, content_md(), delete_last, date)`. `content_md()`
is the [[astro-format]] file (`serializers.serialize`).

Two guards on the write:
- **Empty slug → skip.** `updated()` returns early when `get_slug()` is empty, so a
  title-less model never litters a stray `<date>-.md`.
- **Rename-by-delete (`delete_last`).** When `delete_last` is True (default) and the new
  filename differs from the last-written one, the old file is deleted after writing the
  new — that's how a title/date change *renames* on disk. A `threading.Lock` in
  `filemanager.py` guards the write. `delete_last` is forced False around
  `change_article`, `new_article`, and `new_both_articles` so loading/transitioning
  never deletes a real file. **`new_article` also resets `ContentFile.last_filename`
  to `""`** — a fresh post is not a rename of the one before it. Without that reset a
  blank new article (empty slug → `updated()` skips the write, so `last_filename` is
  never refreshed) left the *previous* article as the deletion target, and the first
  keystroke of the new title rename-by-deleted the post you just left.

## Pull-based UI (no push)

The web frontend gets **no** push notifications from Python. After any mutation, JS
awaits the bridge call then re-fetches `get_state(hl)` and re-renders
(`App.refresh`/`refreshAll`). See [[web-ui]], [[webapi-bridge]].

Consequence — **add a field in two places**: a new model field must be added to both
`get_state` (Python) *and* the `apply()` of the relevant JS module, or the UI won't
show it. Pair-shared fields (`facets`, `draft`) call `refreshAll()` so both columns
update.

Inputs are debounced (~600ms) and skipped while focused (`App.setValue`) so a save
round-trip doesn't clobber what the user is typing.

## See also
- [[article-model]] — the setters and `updated()`
- [[file-storage]] — `filemanager.ContentFile`, the rename-by-delete mechanics
- [[invariants-and-traps]] — these two as hard rules
