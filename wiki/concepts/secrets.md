# Secrets handling

WriterHelper talks to social platforms, so it holds credentials. The rule: **secrets
live only in git-ignored `settings*.ini` on the dev machine; describe location/kind in
the wiki, never the value.**

## Where secrets live

- `settings_bsky_<hl>.ini` — Bluesky `Handle` + `AppPassword` (an app password from
  settings → privacy & security → app passwords, not the account password). See
  [[bluesky-adapter]].
- `settings_x_<hl>.ini` — X/Twitter OAuth fields (`APIKey`, `APISecret`, `AccessToken`,
  `AccessSecret`, `BearerToken`, `ClientID`, `ClientSecret`). See [[x-adapter]].
- `settings_fb_<hl>.ini` — Facebook **and** Instagram: `PageId`, a long-lived Page
  `Token` (the secret), and `IgUserId` (the IG Business account id, not secret). Shared by
  both Meta adapters. See [[facebook-adapter]], [[instagram-adapter]].
- `settings_publish.ini` — publishing knobs (transport pins, hidden platforms, hook
  command, expected account handles, Pinterest boards). **Not secret** — no tokens. See
  [[browser-hook]].
- The [[browser-hook]] platforms (X by default, LinkedIn, Facebook profile, Instagram,
  Threads, Pinterest, TikTok, Medium) hold **no credentials at all**: they post through the
  operator's own signed-in Chrome session.
- `settings_<hl>.ini` — paths + the site base URL (not secret, but user-private; also
  git-ignored). See [[file-storage]].

All `settings*.ini` are covered by `.gitignore`. Never commit them, never paste their
contents into chat.

## LinkedIn incident (resolved)

Credentials had been hardcoded in `post_linkedin.py` and, worse, duplicated into a docs
file. The fix: the docs-file values were **scrubbed from git history** (commits
rewritten) and `post_linkedin.py` was later deleted outright (LinkedIn now posts through
the [[browser-hook]], no developer app).

The leaked `client_secret` / `access_token` should be **revoked** in the LinkedIn
developer console (or the app deleted) — redaction removes the copy, not the validity.

## Rule for the wiki

When documenting an adapter or config, write *what kind* of secret goes *where*
(filename + INI key), never the secret itself. A credential that lands in a wiki page is
a credential in git history. (Mirrors the user's standing `never-duplicate-secrets-in-docs`
memory.)

## See also
- [[invariants-and-traps]] · [[post-base]] · [[browser-hook]] · [[file-storage]]
