# Glossary

Domain language for WriterHelper. One line each; deeper treatment is linked.

- **article** — one blog post: title, content (markdown), tags, excerpt image, optional links, date. Persisted as one `.md` file in the configured `posts` folder. See [[article-model]].
- **hl** — language code (`"fr"` or `"en"`). Threads through everything: model selection, INI filenames, capture output names, translate direction. See [[invariants-and-traps]].
- **ref** — the reciprocal article in the *other* language. `ArticleModel.set_ref(other)` couples FR↔EN in memory; it drives twin loading and pair-shared fields. In Jekyll frontmatter it once surfaced as a `ref:` URL; in Astro it is replaced by `translationKey`. See [[bilingual-pairing]].
- **translationKey** — the Astro pairing key, the *identical* literal value in both languages' files. Minted `<date>-<EN-slug>` (falls back to the current slug while EN is untitled) and **stamped onto BOTH `self` and `ref`** at mint, so the files can't diverge by authoring order; **sticky** once set (`ArticleModel.translation_key`). The value is arbitrary — only matching matters. See [[bilingual-pairing]], [[astro-format]].
- **facet** — a language-independent topic tag on an article *pair*: `dev | physics | fiction | music | ideas` (`serializers.FACETS`). Drives the site's **doors**. Pair-shared via `set_facets`, written `facets: [...]`. **WriterHelper requires ≥1 facet** (authoring-side: `publish` refuses, `prepare_post` returns `facets_ok`, the meta panel flags red); the site's zod schema still allows `[]` for the back-catalog. See [[social-publishing]], [[martingamsby-site]].
- **door** — the Astro site's facet-filtered entry surface; WriterHelper just supplies the `facets` that feed it. See [[martingamsby-site]].
- **draft** — pair-shared bool; `draft: true` in Astro frontmatter hides the post from the site build, omitted to publish. `ArticleModel.draft`, `set_draft`.
- **serializer** — the format seam in `serializers.py`. `serialize(article)` writes the Astro file; `parse(...)` auto-detects Jekyll vs Astro on load. Saved format is **Astro**; Jekyll is load-only. See [[serializers]].
- **slug** — kebab-case id derived from `title` via `unidecode` → lowercase → strip non-alphanumeric (preserves `-`). Used in the filename `YYYY-MM-DD-<slug>.md`. Code: `ArticleModel.get_slug`. See [[article-model]].
- **length category** — `mini` if `len(content) < 280`, `medium` if `> 2000`, else `short`. Surfaces in the UI label only; no longer written to the file (`categories` dropped in Astro). See [[social-publishing]].
- **excerpt_image** — relative image path on the model. Written to Astro frontmatter as `image:` (omitted when empty). Remote URLs get self-hosted by the localize hook. See [[astro-format]].
- **image_thumb / imageThumb** — small (160²) list thumbnail produced by the localize hook alongside the self-hosted `image`. Round-tripped on load so edits never strip it. See [[astro-format]].
- **link** — a `(text, url)` pair in `ArticleModel.links`, rendered into the file footer. Named slots (Medium, Typeshare, X/Twitter, …). See [[link-slots]].
- **content_md flavors** — the five renderings of one article: `content_md` (the saved Astro file, via `serializers.serialize`) plus four HTML flavors in `rendering.py`. See [[content-flavors]].
- **richTextArea capture** — `richTextArea_<slug>_<hl><N>.jpg`. The branded social image, captured page-by-page from the card surface by html2canvas and written by `webapi.save_capture` (name from `publishing.capture_filename`). **JPEG** (also the Instagram asset) and **slug-named** so it's tied to its article. Page 1 is what image-mode publishing attaches. See [[image-card-capture]].
- **card / .card-frame** — the capturable branded image surface in the web UI (was the QML `richTextArea` Rectangle). See [[image-card-capture]].
- **Post (base) + adapters** — `post.py`'s `Post` is the base for `PostBsky`, `PostX`, `PostFB`, and `PostIG` (all inherit). `PostFB` is the Graph API Facebook Page adapter (text/image, no threads); `PostIG` is the Instagram adapter (image-only, public-URL image, reuses the FB token). See [[post-base]], [[facebook-adapter]], [[instagram-adapter]].
- **prepare_post / publish** — the two-phase social-post flow in `publishing.py`. `prepare_post` computes the preview with no side effects; `publish` actually sends the user-confirmed message. See [[social-publishing]].
- **mode (text · thread · image)** — the publish choice in the popup: `"text"` posts the message only; `"thread"` splits it into a reply chain ([[thread-split]]); `"image"` posts message + the page-1 capture (JPEG). Defaulted from `suggested_mode` (text if it fits, else thread), user-overridable. See [[social-publishing]].
- **thread** — a long article posted as a reply chain of platform-sized posts (X, Bluesky). Auto-split at paragraph/sentence/word boundaries with the split points **editable** via `---` lines in the popup textarea; optional ` (i/n)` numbering; first post's URL is the link-slot guard. Code: `thread_split.py` + `Post.post_thread`. See [[thread-split]], [[social-publishing]].
- **bridge / webapi.Api** — the pywebview JS bridge; JS calls `window.pywebview.api.<method>`. UI is pull-based. See [[webapi-bridge]].
- **save_capture** — bridge method that writes one html2canvas page as the slug-named JPEG `richTextArea_<slug>_<hl><page>.jpg`. See [[webapi-bridge]], [[image-card-capture]].
- **updated()** — `ArticleModel.updated()` — a plain method (not a Qt signal) every setter calls on real change; it re-saves the `.md`. See [[auto-save-and-pull-ui]].
- **delete_last** — `ArticleModel` flag (default True); when True, saving a new filename deletes the previously-saved file (rename-by-delete-and-write). Forced False around load/new transitions. See [[auto-save-and-pull-ui]].
- **DEFAULT_TAGS / Gamsblurb** — `DEFAULT_TAGS = "Gamsblurb"` (in `article.py`): the seed tag and the site's house category, always present.
- **tag** — a per-article label (stored as one comma-separated string). Unlike a [[glossary]] facet, a tag is free-er and language-specific (`Health`/`Santé`), but the popular/reused ones now belong to a controlled bilingual vocabulary and stay matched across the FR/EN pair. See [[tag-vocabulary]].
- **tag concept** — one entry in the controlled vocabulary (`tag_vocab.py`): an `{en, fr}` pair (equal for language-neutral tags); its **id is the English label**. Raw labels (casing/typo/synonym/leak variants) fold onto a concept case-insensitively. See [[tag-vocabulary]].
- **tag picker** — the suggestion chips under the Tags input: `matching` (tags co-occurring with this article's facets) + `popular` (overall frequency). Backed by `tag_index.py` + `webapi.tag_suggestions`/`toggle_tag`. See [[tag-vocabulary]].

- **popularity ledger** — `popularity.json` (WriterHelper repo root): an append-only list of dated **snapshots**, each a set of `{key, hl, platform, url, metrics}` **readings** of how a published post is performing on socials. Written by the operator-run `/popularity` sweep; never edited (it's the time series). See [[popularity-tracking]].
- **reading / snapshot** — one platform engagement measurement for one post (`metrics` is a free dict: likes/reposts/views/claps/…); a snapshot is all readings from one sweep, stamped with the run date. See [[popularity-tracking]].

## See also
- [[overview]] — the system in one screen
- [[index]] — full page catalog
