# LinkedIn — BROKEN

⚠️ `post_linkedin.py` is broken dead code. **Do not import, do not wire to UI.**

## What's wrong

- No `class` definition. No function definition either. The file is just a snippet of code at module top level, indented as if it were a method body — so the unexpected indentation would raise `IndentationError` if anything tried to import it.
- Hardcoded credentials in committed source (values intentionally NOT reproduced here):
  - Line 25: `client_id` — LinkedIn app client_id (identifying, not a secret per se)
  - Line 39: `client_secret` — commented out; **rotate it** (was exposed in working source)
  - Line 38: `auth_code` — commented out (short-lived OAuth code, already expired)
  - Line 75: `access_token` — commented out
  - **Line 76: `access_token` — UNCOMMENTED, live-looking token; rotate immediately**
- No INI / config integration. Tokens are baked in.

## What it was trying to do

- Use LinkedIn's `/v2/shares` REST endpoint.
- Post the article's title with the website URL as the entity location and `richTextArea_en1.png` as a thumbnail (using a constructed `image_path` that's wrong: `os.path.join(os.path.realpath(__file__), "richTextArea_en1.png")` — `realpath(__file__)` returns the *file* path, not a directory, so the join produces an invalid path).
- Hardcoded `person_id = "martingamsby"` as the LinkedIn URN owner.

## Status

- Not imported anywhere in the project (`grep` confirms).
- Not referenced by QML.
- The `LinkedIn` link slot in `ArticleMeta.qml` is a plain text field, not a posting trigger.

## If/when LinkedIn posting is revived

1. **Rotate the leaked `access_token` immediately** (LinkedIn → app developer console → revoke). Even though it's expired, do not assume.
2. Decide on a token storage approach: subclass `Post` with `Token` (or full OAuth2 fields) in `[Access]`, and load from `settings_linkedin_<hl>.ini`.
3. Rewrite as a proper class with a `post(msg, image_local_url, alt_text)` method that returns the post URL.
4. Wire into `ArticleMeta.qml` similar to X/Bluesky (clickable link label → `post_linkedin()` slot on `ArticleModel`).

## See also
- [summary.md](summary.md)
- [post-base.md](post-base.md)
- [../practices.md](../practices.md)
