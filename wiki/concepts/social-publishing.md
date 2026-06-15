# Social publishing — two-phase, behind a popup

Publishing to a social platform is **two-phase**: a side-effect-free `prepare_post`
that fills a confirmation popup, then a `publish` that actually sends only what the user
confirmed. Code: `publishing.py` ([[publishing]]) + `js/publish.js`. This replaced the
old "click a link label → instant post".

## The three modes (text · thread · image)

A post is sent one of three ways, chosen by radio in the popup:

- **text** — post the rendered plain text as one post.
- **thread** — split the plain text into a reply chain of posts that each fit the limit
  ([[thread-split]]); the author can **edit where it splits** (see below).
- **image** — post the **title** only, attaching `richTextArea_<hl>1.png` (page 1 of the
  captured card, [[image-card-capture]]).

The suggestion hinges on the **rendered plain-text length** vs the platform's char limit
(not the `mini`/`medium` UI [[glossary]] length category): fits → `suggested_mode="text"`;
doesn't fit → `suggested_mode="thread"`. `prepare_post` computes this; the popup defaults
to it but the user can override to any mode.

## Editable split points (Thread mode)

`prepare_post` returns `thread_text`: the auto-split segments joined by `---` lines
([[thread-split]] `join_for_edit`). The popup loads that into the textarea; the author
moves/adds/removes `---` lines to control the breaks. A live per-segment readout shows
`#i len/max` (red when over), accounting for the projected ` (i/n)` counter when numbering
is on. Publish is blocked while any segment is over the limit. Two checkboxes:
**Number posts (1/n)** (default on) and **Attach card image to first post** (default off,
disabled until the PNG is grabbed).

## `prepare_post(article, platform_key) → dict` — NO side effects

Safe to call every time the popup opens. Returns: `text` (`rendering.plain_text`),
`text_length`, `fits` (≤ max_length), `suggested_mode`, `existing_url` (idempotence
guard), `title`, `image_file` (`richTextArea_<hl>1.png`), `image_exists`,
`image_data_url` (base64 if present), `max_length`, `label`, **`facets_ok`** (≥1 facet —
the mandatory-facets gate, see [[glossary]]), and the thread seed `thread_text` /
`thread_count` / `separator` ([[thread-split]]).

## `publish(article, platform_key, mode, message, options=None) → {ok, url, error}`

The only method with side effects. `options` carries thread choices
`{"number": bool, "image": bool}`.
1. No facet → refused (facets are mandatory).
2. Existing link for the slot → `{ok: False, url: existing, error}`. (Clear it to re-post.)
3. `mode == "thread"` → `_publish_thread`: split `message` on `---`, optionally number,
   reject any over-limit segment, post the reply chain via `poster.post_thread`; the
   **first** post's URL becomes the slot guard (`urls[]` also returned). [[thread-split]]
4. `mode == "image"` → requires the PNG on disk; posts `message` + that PNG, alt text =
   full article plain text.
5. `mode == "text"` → re-checks `len(message) <= max_length`; posts text only.
6. On success → `set_link(slot, url)` (re-saves the footer, [[link-slots]]) +
   `webbrowser.open(url)`.

## `PLATFORMS` registry

| key | label | link slot | max_length | adapter |
|---|---|---|---|---|
| `bluesky` | Bluesky | `Bluesky` | 300 | `PostBsky(hl)` ([[bluesky-adapter]]) |
| `x` | X / Twitter | `X/Twitter` | 280 | `PostX(hl)` ([[x-adapter]]) |

`make_poster` imports the adapter lazily, so a missing/broken adapter doesn't break
import and tests can monkeypatch the registry.

## The popup (`js/publish.js`)

`Publish.open(hl, platform)` calls `prepare_post`, seeds per-mode drafts (text = full
text, thread = `thread_text`, image = title), and renders the modal: three radio modes
(text · thread · image) defaulted to `suggested_mode`, an **editable** textarea (switching
modes swaps the remembered draft). In text/image mode a live `count / max_length` (red
when over) + the PNG preview in image mode; in thread mode the per-segment readout +
the Number/Image checkboxes (see *Editable split points* above). Publish is disabled when
over the limit, when text is empty, in image mode when the PNG is missing, or in thread
mode when any segment is over. If already posted, it shows the existing URL + a "Clear
link (allow re-post)" button.

## Invariants
- Nothing is sent until **Publish** is clicked; opening the popup is read-only.
- The idempotence guard (existing link) is enforced in BOTH `prepare_post` display and
  `publish` execution.
- Editing the message in the popup does NOT change the article; `message` goes straight
  to the poster.

## See also
- [[publishing]] · [[post-base]] · [[bluesky-adapter]] · [[x-adapter]]
- [[image-card-capture]] — produces the PNG image mode attaches
- [[link-slots]] — where the returned URL is stored
