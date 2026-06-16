# Invariants & traps

The non-negotiables and the landmines. Break an invariant and something silently stops
working; step on a trap and you waste an hour.

## Invariants (do not break)

- **Auto-save**: every `ArticleModel` setter mutates then calls `self.updated()`, which
  writes the file and deletes the previously-saved one (rename-by-delete). No save
  button. New setter → `if self.x != value: self.x = value; self.updated()`. See
  [[auto-save-and-pull-ui]].
- **UI is pull-based**: no push. After any mutation JS re-fetches `get_state(hl)`. A new
  field must be added to BOTH `get_state` (Python) and the JS module's `apply()`.
- **Capture naming is load-bearing AND identity-bearing**:
  `richTextArea_<slug>_<hl><N>.jpg` (JPEG). The name comes from the single source of
  truth `publishing.capture_filename(article, page)`; `capture.js` → `save_capture`
  writes it, `publishing` reads page 1 via `image_filename` for image mode. **Slug-naming
  is the "right article" guarantee** — publishing resolves the current article's slug, so
  a stale grab from another post isn't found. Change one side, change both. See
  [[image-card-capture]].
- **`hl` thread**: the same `hl` string flows model → INI filenames
  (`settings_<hl>.ini`, `settings_bsky_<hl>.ini`, `settings_x_<hl>.ini`) → capture name →
  atproto `langs=[hl]`. Keep it consistent.
- **Publish is two-phase + guarded**: `prepare_post` has no side effects; only `publish`
  sends. `publish` refuses an existing-link slot, a no-facet article, and re-checks the
  char limit / PNG existence. See [[social-publishing]].
- **Translate is one-way, fills only empties**: `translate(hl)` aborts if the
  destination has content. See [[machine-translation]].
- **A `data:` image must never be left persisted**: a dropped/opened image enters as a
  `data:` URL ([[image-card-capture]] / [[astro-format]]) and is fine as *input*, but if
  the self-host hook can't turn it into `…header.webp`, `_localize_excerpt_image` retries
  once and then **drops** it (clears + re-saves) rather than commit a 100KB+ base64 blob
  into the post. A plain remote http(s) URL that fails is left in place (small, still
  renders). See [[astro-format]].
- **`change_article` splits on `---` into 3-or-4 parts**: frontmatter / body / optional
  footer. Anything else fails parse silently (`Couldn't parse the md file`).
- **Facets are mandatory (authoring-side)**: `publish` refuses a no-facet article;
  `prepare_post` returns `facets_ok`; the meta panel flags red. The site's zod schema
  still allows `[]`. See [[glossary]].
- **No public data attributes on `webapi.Api`**: hold state as `_articles` / `_window`.
  A *public* non-callable attr makes pywebview's bridge-injection walk recurse into
  `window.native` (.NET Form) forever → startup crash. Methods are safe. See
  [[webapi-bridge]].
- **Every new `Post` subclass needs an `[Access]` INI** + a `config_filename` override.
  The base falls back to `settings_TODO_<hl>.ini` — the smoke signal of a missed
  override. See [[post-base]].

## Traps

- **`model.py` (~727 lines) is LEGACY.** The live code is the Qt-free split
  ([[article-model]] / [[rendering-module]] / [[articles-model]] / [[publishing]]).
  `model.py` + `backend.py` serve only `writerhelper_qt.py`. Edit the new modules.
- **Two entry points**: `writerhelper.py` = pywebview/web (primary);
  `writerhelper_qt.py` = old QML (legacy). See [[legacy-qt-ui]].
- **Do not run the Qt path now**: `model.py` still emits Jekyll into the repointed Astro
  folders — it would write `layout`/`categories` files (no `translationKey`) into the
  blog and break the site build.
- **`dev.html` + `js/dev-mock.js`** are browser-only dev aids (fake `window.pywebview`),
  never loaded by the real app. `dev.html` must be saved UTF-8 — PowerShell
  `Get-Content`/`Out-File` mangle the non-ASCII `→`; use the Write tool or HTML entities.
- **`post_linkedin.py` is broken dead code** — unindented snippet, never committed, do
  not import. See [[linkedin-adapter]], [[secrets]].
- **`post_fb.PostFB` now inherits `Post`** and is wired into the UI (Facebook publish
  button, both langs). It has no
  `post_thread` (text/image only). See [[facebook-adapter]].
- **`settings_<hl>.ini` point at the Astro repo** (`martingamsby.com/src/content/blog/<hl>`)
  with base URL `https://martingamsby.com/<hl>/blog/`. Git-ignored. See [[file-storage]].
- **Cruft — ignore, never pattern-match from**: `model - Copy*.py`,
  `qtquickcontrols2.conf_NOPE`, `test.html`, `all_content_fr.txt`, `posts.txt`.

## Tests

`tests/` covers the Qt-free layer: `test_article.py` (slug, length category,
save/rename, links, `change_article` round-trip, V2, ref) and `test_publishing.py`
(`prepare_post` decision, `publish` with a fake poster + monkeypatched `PLATFORMS`).
`conftest.py` wires an `ArticlesModel` to temp posts folders + temp INIs via
`config_dir`. Run `python -m pytest tests -q`. No Qt, no pywebview needed.

## Style

- New source files ≤350 lines (CLAUDE.md mandate); wiki pages ≤250.
- 4-space indentation in Python and the web JS/CSS.
- Python uses `# ====` decorative banner dividers — match locally if extending, don't
  add to fresh files.
- Frontend: vanilla JS, no build step, no framework; html2canvas vendored so the
  packaged app works offline.

## See also
- [[secrets]] · [[auto-save-and-pull-ui]] · [[social-publishing]] · [[webapi-bridge]]
