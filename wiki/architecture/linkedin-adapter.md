# LinkedIn adapter (`post_linkedin.py`) — BROKEN

⚠️ Broken dead code. **Do not import, do not wire to the UI.**

## What's wrong

- **No `class` or function definition** — the file is a snippet of code at module top
  level, indented as if it were a method body, so importing it would raise
  `IndentationError`.
- **Hardcoded credentials** were committed (values intentionally not reproduced here):
  `client_id`, a commented `client_secret`, a commented expired `auth_code`, and an
  **uncommented live-looking `access_token`**. See the incident in [[secrets]].
- No INI/config integration — tokens are baked in.

## What it was trying to do

Use LinkedIn's `/v2/shares` REST endpoint to post the article title + website URL with
`richTextArea_en1.png` as a thumbnail (via a wrong path built from
`os.path.realpath(__file__)`), with `person_id = "martingamsby"` as the URN owner.

## Status

Not imported anywhere; not referenced by QML. The LinkedIn link slot in the meta UI is a
plain text field ([[link-slots]]), not a posting trigger.

## If revived

1. **Rotate the leaked `client_secret` / `access_token`** in the LinkedIn developer
   console first ([[secrets]]).
2. Subclass [[post-base]] with proper `[Access]` fields →
   `settings_linkedin_<hl>.ini`.
3. Rewrite as a class with `post(msg, image_local_url, alt_text) → URL`.
4. Wire into the meta column like X/Bluesky.

## See also
- [[secrets]] · [[post-base]] · [[invariants-and-traps]]
