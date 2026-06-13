# Practices, Invariants, Traps

## Invariants (do not break)

- **Auto-save**: every setter on `article.ArticleModel` mutates state then calls `self.updated()` (a plain method now, not a Qt Signal); `updated()` calls `ContentFile.create_file`, which writes the new file *and deletes the previously-saved file* (rename-by-delete-and-write). There is no explicit save button. New setter → follow `if self.x != value: self.x = value; self.updated()`.
- **UI is pull-based**: the web frontend does not get push notifications. After any mutation, JS calls `webapi.get_state(hl)` again and re-renders. If you add a field, add it to both `get_state` (Python) and the `apply()` of the relevant JS module.
- **PNG output naming is load-bearing**: `richTextArea_<hl><N>.png`. The web capture (`capture.js` → `webapi.save_capture`) writes this exact pattern; `publishing.image_filename` / `publish` read `richTextArea_<hl>1.png` for image mode. Don't rename without updating both sides. (Legacy QML `grabCallback` also uses it.)
- **`hl` thread**: same `hl` string flows model → INI filenames (`settings_<hl>.ini`, `settings_bsky_<hl>.ini`, `settings_x_<hl>.ini`) → PNG name → atproto `langs=[hl]`. Keep it consistent.
- **Publish is two-phase + guarded**: `prepare_post` has NO side effects (safe to call on popup open); only `publish` sends. `publish` refuses if a link already exists for the slot (clear it to re-post) and re-checks the platform char limit / PNG existence. See [posting/popup-flow.md](posting/popup-flow.md).
- **Translate is one-way and only fills empties**: `ArticlesModel.translate(hl)` aborts if `dst.content` is non-empty. Source is `hl`, destination is the other language. See [model/translation.md](model/translation.md).
- **`change_article` parses 3-or-4 part split on `---`**: frontmatter (part 1), body (part 2), optional footer (part 3). Anything else fails parse silently with `Couldn't parse the md file`.
- **Every new `Post` subclass needs an `[Access]` INI** and a `config_filename` override. The base falls back to `settings_TODO_<hl>.ini` if not overridden — that's the smoke signal of a missed override. See [posting/post-base.md](posting/post-base.md).

## Traps

- **`model.py` (727 lines) is now LEGACY.** The Qt-free split is the live code: `article.py` (ArticleModel), `rendering.py` (content_md flavors + image embedding), `articles.py` (ArticlesModel + translate), `publishing.py` (post flow). `model.py` + `backend.py` are imported only by `writerhelper_qt.py`. Edit the new modules, not `model.py`.
- **Two entry points**: `writerhelper.py` = pywebview/web (primary); `writerhelper_qt.py` = old QML (legacy fallback). Don't confuse them.
- **`dev.html` + `js/dev-mock.js`** are browser-only dev aids (fake `window.pywebview`). Never loaded by the real app. `dev.html` must be written as UTF-8 — PowerShell `Get-Content`/`Out-File` mangles non-ASCII (the `→` chars); use the Write tool or HTML entities.
- **`post_linkedin.py` is broken dead code**. No class definition, just unindented snippet at module top level. It is untracked (never committed). Its `client_id`, `client_secret`, `auth_code`, and `access_token` values are now redacted to `REDACTED_ROTATE_THIS` in the working file. Do not import; do not wire to UI. The exposed LinkedIn `client_secret` and `access_token` must still be **rotated** in the LinkedIn developer console — redaction removes the copy, not the validity.
- **`post_fb.PostFB` does NOT inherit `Post`** and uses a different INI key shape (`Token`, `PageId` not `Handle`, `AppPassword`). It is also not wired into the QML UI; FB posting is currently manual via the CheckList. See [posting/facebook.md](posting/facebook.md).
- **`settings_<hl>.ini` now point at the Astro repo** (`martingamsby.com/src/content/blog/<hl>`) with the Astro base URL (`https://martingamsby.com/<hl>/blog/`) — the hard switch to the Astro write format. They are git-ignored (user-private). The old Jekyll paths (incl. the historical `martingamsby.gitbub.io_en` typo folder) are no longer used. ⚠️ The legacy Qt path (`model.py`) still emits Jekyll into whatever `posts` points at — do not run it now (see [ui/summary.md](ui/summary.md)).
- **Cruft files — ignore, do not pattern-match from**:
  - `model - Copy.py`, `model - Copy (2).py`, `model - Copy (3).py` — old backups
  - `qtquickcontrols2.conf_NOPE` — deactivated config
  - `test.html` — scratch
  - `all_content_fr.txt` — output of `Backend.get_all_articles("fr")` from a commented-out one-shot in `Backend.__init__`

## Secrets

- Local secrets live in `settings*.ini` (covered by `.gitignore`). Real BlueSky AppPassword and X API credentials are in `settings_bsky_<hl>.ini` and `settings_x_<hl>.ini` on the dev machine — never commit, never paste into chat.
- LinkedIn creds: the values once duplicated into `memory/posting/linkedin.md` were scrubbed from git history (commits rewritten), and `post_linkedin.py`'s values are redacted in the working tree. Never reproduce secret values in Memory files — describe location/kind only. See [posting/linkedin.md](posting/linkedin.md).

## Tests

- `tests/` holds pytest coverage of the Qt-free layer: `test_article.py` (slug, length category, save/rename, links, `change_article` round-trip, V2, ref) and `test_publishing.py` (`prepare_post` decision, `publish` flow with a fake poster + monkeypatched `PLATFORMS`). `conftest.py` wires an `ArticlesModel` to temp posts folders + temp INIs via `config_dir`. Run: `python -m pytest tests -q`. These import the new modules directly — no Qt, no pywebview needed.

## Style

- File editing: keep new files ≤350 lines (CLAUDE.md mandate). Memory files ≤250 lines. The web JS modules are each single-responsibility and small for this reason.
- Indentation: 4 spaces in Python and in the web JS/CSS.
- Comments: existing Python uses `# ====` decorative banners as section dividers — match the local style if extending a file, but don't add new ones to fresh files.
- Frontend: vanilla JS, no build step, no framework. html2canvas is vendored (`web/vendor/`), not from a CDN, so the packaged app works offline.

## See also
- [summary.md](summary.md)
- [terminology.md](terminology.md)
- [posting/linkedin.md](posting/linkedin.md)
- [posting/facebook.md](posting/facebook.md)
