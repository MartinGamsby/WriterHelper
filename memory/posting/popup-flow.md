# Publish Confirmation Popup

The core change from the old "click a link label → instant post" behavior: publishing is now **two-phase** so the user previews and confirms exactly what is sent.

## Backend — `publishing.py`

`PLATFORMS` registry maps key → `Platform(key, label, link_name, max_length, make_poster)`:

| key | label | link slot | max_length | adapter |
|---|---|---|---|---|
| `bluesky` | Bluesky | `Bluesky` | 300 | `PostBsky(hl)` |
| `x` | X / Twitter | `X/Twitter` | 280 | `PostX(hl)` |

`make_poster` imports the adapter lazily (so a missing/broken adapter doesn't break import, and tests can monkeypatch the registry).

### `prepare_post(article, platform_key) -> dict` — NO side effects
Computes: `text` (rendered plain text, `rendering.plain_text`), `text_length`, `fits` (≤ max_length), `suggested_mode` (`text` if fits else `image`), `existing_url` (idempotence guard value), `title`, `image_file` (`richTextArea_<hl>1.png`), `image_exists`, `image_data_url` (base64 if present), `max_length`, `label`. Safe to call every time the popup opens.

### `publish(article, platform_key, mode, message) -> {ok, url, error}`
The only method with side effects.
1. If a link already exists for the slot → `{ok: False, url: existing, error}`. (Clear it to re-post.)
2. `mode == "image"`: requires `richTextArea_<hl>1.png` on disk; posts `message` + that PNG, alt text = full article plain text.
3. `mode == "text"`: re-checks `len(message) <= max_length`; posts text only.
4. On success: `set_link(slot, url)` (re-saves the `.md` footer) + `webbrowser.open(url)`.

## Frontend — `js/publish.js`

`Publish.open(hl, platform)` calls `prepare_post`, seeds per-mode drafts (`text` draft = full text, `image` draft = title), and renders the modal.

The modal shows:
- Title "Publish to <label> — <HL>".
- If already posted: a warning with the existing URL + a "Clear link (allow re-post)" button (calls `clear_link`, then reopens) and Close.
- Otherwise: two radio modes (Text post / Title + image) defaulted to `suggested_mode`, an **editable** `<textarea>` (switching modes swaps the remembered draft), a live `count / max_length` (red when over), and in image mode the captured PNG preview or a "not found — use Grab first!" note.
- Publish is disabled when over the limit, when text is empty, or in image mode when the PNG is missing.

`send()` calls `publish`, then either shows a success panel with the clickable URL or surfaces `result.error` inline.

## Invariants
- Nothing is sent until the user clicks **Publish**. Opening the popup is read-only.
- The idempotence guard (existing link) is enforced in BOTH `prepare_post` display and `publish` execution.
- Editing the message in the popup does NOT change the article; `message` is passed straight to the poster.

## See also
- [summary.md](summary.md)
- [../model/post-routing.md](../model/post-routing.md)
- [../web-ui/capture.md](../web-ui/capture.md) — produces the PNG image mode attaches
- [post-base.md](post-base.md)
