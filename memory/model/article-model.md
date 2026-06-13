# ArticleModel

Pure-Python `ArticleModel` in `article.py` (Qt-free; the active web stack uses it).
One instance per language (`hl="fr"` or `hl="en"`). The legacy Qt twin lives in
`model.py` — see [../ui/summary.md](../ui/summary.md).

## State (instance attributes)

- `hl: str` — language code; threads through INI loading, file naming, social posts.
- `title`, `content`, `excerpt_image`, `tags` (default `"Gamsblurb"`), `date`
  (default today, `YYYY-MM-DD`).
- `facets: list[str]` — pair-shared; `dev|physics|fiction|music|ideas`. Drives the
  Astro site's "doors".
- `draft: bool` — pair-shared; `draft: true` hides the post from the site build.
- `translation_key: str` — sticky pairing key (see below). `""` until generated.
- `links: list[Link]` — populated via `set_link(text, url)`.
- `mini`, `medium` — length category flags (see [post-routing.md](post-routing.md)).
- `green`, `black` — title-color toggles for the image surface.
- `ref: ArticleModel | None` — the paired other-language model, set via `set_ref`.
- `delete_last` (default True) — gates rename-by-delete in `updated()`.
- `content_file: ContentFile`, `config: ConfigParser` (`settings_<hl>.ini`).

## updated() — the save hook

Not a Qt signal anymore: a plain method every setter calls on a real change. It
writes the file via `content_file.create_file(folder, slug, content_md(), delete_last,
date)` — but **returns early when `get_slug()` is empty** (a title-less model has no
filename, so it must not write a stray `<date>-.md`). `content_md()` returns the
**Astro** file (`serializers.serialize`). The JS layer drives re-render separately by
re-fetching `get_state` (pull-based).

## Setters

Each `set_*` persists via `updated()` only on a real change:
`set_title/date/content/tags/excerpt_img/posts_folder/website_url/green/black`.

Pair-shared setters mirror the value onto `ref` (like `date`) and save both:
- `set_facets(list)` — cleans + mirrors `facets`.
- `set_draft(bool)` — mirrors `draft`.

## Astro pairing + URLs

- `get_translation_key()` — sticky pairing key. If unset, adopts the ref's key, else
  mints `<date>-<EN-slug>` (falls back to own slug while EN untitled) and **stamps it
  on BOTH self and ref** so the pair can't diverge across authoring orders. Frozen
  once set; no disk write in the getter. See
  [../file-storage/astro-format.md](../file-storage/astro-format.md).
- `get_post_url()` — public Astro URL `<website><date>-<slug>/`. Used for the
  "Based on"/"Basé sur" seed link (and the URL social posts share).
- `get_ref()` — `ref.website_url + ref.slug` (the old Jekyll `ref:` URL). Retained
  but no longer in saved output (Astro uses `translationKey`).

## Rendering flavors

`content_md()` → `serializers.serialize(self)` (the saved Astro file). The other
flavors (`content_md_rich/separators/separators_br/content_short`) delegate to
`rendering.py` and are unchanged — they render the visual card/social text, not the
saved file. See [rendering.md](rendering.md).

## Navigation

- `open_last_article()` / `open_article()` (file dialog) / `open_prev_article()` /
  `open_next_article()` — scan/walk `posts_folder` `.md` files and load via
  `change_article`.
- `new_article(copy_current=False)` — clears state; resets `translation_key` (fresh
  key). With `copy_current=True`: keeps content, title suffixed " V2", seeds the
  "Based on" link to `get_post_url()`; keeps `facets`/`draft`.
- `new_both_articles(copy_current)` — `ref.new_article` then `self.new_article`,
  with `delete_last=False` around the pair.

## change_article(file_contents, old_date, change_ref=True)

Thin wrapper over `serializers.parse(self, ...)`. Format (Jekyll vs Astro) is
auto-detected and routed; Astro twins resolve by `translationKey` scan, Jekyll twins
by ref-URL filename. `delete_last` forced False during load. See
[../file-storage/astro-format.md](../file-storage/astro-format.md).

## Slug rule

`get_slug()` = `unidecode(title)` → `.`/` `→`-` → collapse repeated `-` → lowercase
→ strip non-alphanumeric (preserves `-`) → trim trailing `-`. Drives the filename and
(via the EN slug) the `translationKey`.

## See also
- [articles-model.md](articles-model.md)
- [rendering.md](rendering.md)
- [post-routing.md](post-routing.md)
- [links.md](links.md)
- [../file-storage/astro-format.md](../file-storage/astro-format.md)
