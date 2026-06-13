# ArticleModel (`article.py`)

Pure-Python `ArticleModel` — Qt-free, used by the active web stack. One instance per
language (`hl="fr"` or `hl="en"`). The legacy Qt twin is in `model.py`
([[legacy-qt-ui]]).

## State (instance attributes)

- `hl` — language code; threads through INI loading, file naming, social posts.
- `title`, `content`, `excerpt_image`, `tags` (default `"Gamsblurb"`), `date`
  (default today, `YYYY-MM-DD`).
- `facets: list[str]` — pair-shared; `dev|physics|fiction|music|ideas`. Drives the
  site's [[glossary]] doors; **≥1 required to publish**.
- `draft: bool` — pair-shared; `draft: true` hides the post from the site build.
- `translation_key: str` — sticky pairing key, `""` until set. See [[bilingual-pairing]].
- `links: list[Link]` — via `set_link(text, url)`. See [[link-slots]].
- `mini`, `medium` — length-category flags.
- `green`, `black` — title-color toggles for the image surface.
- `ref: ArticleModel | None` — the paired other-language model (via `set_ref`).
- `delete_last` (default True) — gates rename-by-delete in `updated()`.
- `content_file: ContentFile`, `config: ConfigParser` (`settings_<hl>.ini`).

## updated() — the save hook

A plain method every setter calls on a real change. Writes via
`content_file.create_file(folder, slug, content_md(), delete_last, date)` — but
**returns early when `get_slug()` is empty** (no stray `<date>-.md`). `content_md()` is
the [[astro-format]] file. Re-render is driven separately by the JS re-fetching
`get_state` (pull-based). See [[auto-save-and-pull-ui]].

## Setters

Each `set_*` persists via `updated()` only on a real change:
`set_title/date/content/tags/excerpt_img/posts_folder/website_url/green/black`.
Pair-shared setters mirror onto `ref` and save both: `set_facets(list)` (cleans +
mirrors), `set_draft(bool)`.

## Astro pairing + URLs

- `get_translation_key()` — sticky key: return own → adopt ref's → mint and **stamp
  both** (no disk write in the getter). Full rules in [[bilingual-pairing]].
- `get_post_url()` — public Astro URL `<website><date>-<slug>/`; used for the "Based on"
  seed link and the URL social posts share.
- `get_ref()` — `ref.website_url + ref.slug` (the old Jekyll `ref:` URL). Retained but
  not in saved output.

## Navigation

- `open_last_article()` / `open_article()` (file dialog) / `open_prev_article()` /
  `open_next_article()` — scan/walk `posts_folder` `.md` files, load via `change_article`.
- `new_article(copy_current=False)` — clears state; resets `translation_key`. With
  `copy_current=True` ("Make V2"): keeps content, title suffixed " V2", seeds the "Based
  on" link to `get_post_url()`, keeps `facets`/`draft`.
- `new_both_articles(copy_current)` — `ref.new_article` then `self.new_article`, with
  `delete_last=False` around the pair.

## change_article(file_contents, old_date, change_ref=True)

Thin wrapper over `serializers.parse(self, ...)` — format auto-detected and routed,
twins resolved, `delete_last` forced False during load. See [[serializers]].

## Slug rule

`get_slug()` = `unidecode(title)` → `.`/` `→`-` → collapse repeated `-` → lowercase →
strip non-alphanumeric (preserves `-`) → trim trailing `-`. Drives the filename and (via
the EN slug) the `translationKey`.

## See also
- [[articles-model]] · [[rendering-module]] · [[link-slots]] · [[astro-format]]
