# Practices, Invariants, Traps

## Invariants (do not break)

- **Auto-save**: every `set_*` slot on `ArticleModel` mutates state then emits `updated`; the connected `on_updated` calls `ContentFile.create_file`, which writes the new file *and deletes the previously-saved file* (rename-by-delete-and-write). There is no explicit save button. If you add a property setter, follow the same `if self.x != value: self.x = value; self.updated.emit()` pattern.
- **PNG output naming is load-bearing**: `richTextArea_<hl><N>.png`. The QML `grabCallback` chain saves with this exact pattern; `ArticleModel.post` reads `richTextArea_<hl>1.png` as the image fallback. Don't rename without updating both sides.
- **`hl` thread**: same `hl` string flows model → INI filenames (`settings_<hl>.ini`, `settings_bsky_<hl>.ini`, `settings_x_<hl>.ini`) → PNG name → atproto `langs=[hl]`. Keep it consistent.
- **Translate is one-way and only fills empties**: `ArticlesModel.translate(hl)` aborts if `dst.content` is non-empty. Source is `hl`, destination is the other language. See [model/translation.md](model/translation.md).
- **`change_article` parses 3-or-4 part split on `---`**: frontmatter (part 1), body (part 2), optional footer (part 3). Anything else fails parse silently with `Couldn't parse the md file`.
- **Every new `Post` subclass needs an `[Access]` INI** and a `config_filename` override. The base falls back to `settings_TODO_<hl>.ini` if not overridden — that's the smoke signal of a missed override. See [posting/post-base.md](posting/post-base.md).

## Traps

- **`model.py` is 727 lines**, over CLAUDE.md's 350-line limit. Do not extend without first decomposing. Natural seams: rendering (`content_md_*` family) → its own file; `change_article` parser → its own file; the social-post helper `post()` → its own file.
- **`post_linkedin.py` is broken dead code**. No class definition, just unindented snippet at module top level. Hardcoded credentials live in committed source: `client_id` (line 25), commented `client_secret` (line 39), commented `auth_code` (line 38), and an uncommented `access_token` (line 76). Do not import; do not wire to UI. Token rotation/scrub is a separate task.
- **`post_fb.PostFB` does NOT inherit `Post`** and uses a different INI key shape (`Token`, `PageId` not `Handle`, `AppPassword`). It is also not wired into the QML UI; FB posting is currently manual via the CheckList. See [posting/facebook.md](posting/facebook.md).
- **`settings_en.ini` has a typo path**: `martingamsby.gitbub.io_en` (should be `github`). Real folder on disk uses the typo too — do not "fix" the INI without first renaming the folder.
- **Cruft files — ignore, do not pattern-match from**:
  - `model - Copy.py`, `model - Copy (2).py`, `model - Copy (3).py` — old backups
  - `qtquickcontrols2.conf_NOPE` — deactivated config
  - `test.html` — scratch
  - `all_content_fr.txt` — output of `Backend.get_all_articles("fr")` from a commented-out one-shot in `Backend.__init__`

## Secrets

- Local secrets live in `settings*.ini` (covered by `.gitignore`). Real BlueSky AppPassword and X API credentials are in `settings_bsky_<hl>.ini` and `settings_x_<hl>.ini` on the dev machine — never commit, never paste into chat.
- The exception is `post_linkedin.py` (see Traps above), which has tokens in committed source.

## Style

- File editing: keep new files ≤350 lines (CLAUDE.md mandate). Memory files ≤250 lines.
- Indentation: 4 spaces in Python, default in QML.
- Comments: existing code uses `# ====` decorative banners as section dividers — match the local style if extending a file, but don't add new ones to fresh files.

## See also
- [summary.md](summary.md)
- [terminology.md](terminology.md)
- [posting/linkedin.md](posting/linkedin.md)
- [posting/facebook.md](posting/facebook.md)
