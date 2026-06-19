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
- `settings_postbridge.ini` — post-bridge.com `[Access] ApiKey` (the `pb_live_…` key, the
  secret); one hl-independent file for every post-bridge platform. Optional `[Accounts]`
  pins (account ids) are not secret. See [[post-bridge-adapter]].
- `settings_<hl>.ini` — paths + the site base URL (not secret, but user-private; also
  git-ignored). See [[file-storage]].

All `settings*.ini` are covered by `.gitignore`. Never commit them, never paste their
contents into chat.

## LinkedIn incident (resolved)

Credentials had been hardcoded in `post_linkedin.py` and, worse, duplicated into a docs
file. The fix: the docs-file values were **scrubbed from git history** (commits
rewritten) and `post_linkedin.py`'s values redacted in the working tree. The adapter
stays broken/unused ([[linkedin-adapter]]).

If LinkedIn is ever revived, **rotate the leaked `client_secret` / `access_token`** in
the LinkedIn developer console first — redaction removes the copy, not the validity.

## Rule for the wiki

When documenting an adapter or config, write *what kind* of secret goes *where*
(filename + INI key), never the secret itself. A credential that lands in a wiki page is
a credential in git history. (Mirrors the user's standing `never-duplicate-secrets-in-docs`
memory.)

## See also
- [[invariants-and-traps]] · [[post-base]] · [[linkedin-adapter]] · [[file-storage]]
