# Social publishing — two-phase, behind a popup

Publishing to a social platform is **two-phase**: a side-effect-free `prepare_post`
that fills a confirmation popup, then a `publish` that actually sends only what the user
confirmed. Code: `publishing.py` ([[publishing]]) + `js/publish.js`. This replaced the
old "click a link label → instant post".

## The decision (text vs image)

The fallback hinges on the **rendered plain-text length** vs the platform's char limit
(not the `mini`/`medium` UI [[glossary]] length category):

- Fits the limit → post the text only, no image.
- Doesn't fit → post the **title** only, attaching `richTextArea_<hl>1.png` (page 1 of
  the captured card, [[image-card-capture]]).

`prepare_post` computes this as `suggested_mode`; the popup defaults to it but the user
can override.

## `prepare_post(article, platform_key) → dict` — NO side effects

Safe to call every time the popup opens. Returns: `text` (`rendering.plain_text`),
`text_length`, `fits` (≤ max_length), `suggested_mode`, `existing_url` (idempotence
guard), `title`, `image_file` (`richTextArea_<hl>1.png`), `image_exists`,
`image_data_url` (base64 if present), `max_length`, `label`, and **`facets_ok`** (≥1
facet — the mandatory-facets gate, see [[glossary]]).

## `publish(article, platform_key, mode, message) → {ok, url, error}`

The only method with side effects:
1. Existing link for the slot → `{ok: False, url: existing, error}`. (Clear it to re-post.)
2. No facet → refused (facets are mandatory).
3. `mode == "image"` → requires the PNG on disk; posts `message` + that PNG, alt text =
   full article plain text.
4. `mode == "text"` → re-checks `len(message) <= max_length`; posts text only.
5. On success → `set_link(slot, url)` (re-saves the footer, [[link-slots]]) +
   `webbrowser.open(url)`.

## `PLATFORMS` registry

| key | label | link slot | max_length | adapter |
|---|---|---|---|---|
| `bluesky` | Bluesky | `Bluesky` | 300 | `PostBsky(hl)` ([[bluesky-adapter]]) |
| `x` | X / Twitter | `X/Twitter` | 280 | `PostX(hl)` ([[x-adapter]]) |

`make_poster` imports the adapter lazily, so a missing/broken adapter doesn't break
import and tests can monkeypatch the registry.

## The popup (`js/publish.js`)

`Publish.open(hl, platform)` calls `prepare_post`, seeds per-mode drafts (text draft =
full text, image draft = title), and renders the modal: two radio modes defaulted to
`suggested_mode`, an **editable** textarea (switching modes swaps the remembered draft),
a live `count / max_length` (red when over), and the PNG preview in image mode (or a
"not found — use Grab first!" note). Publish is disabled when over the limit, when text
is empty, or in image mode when the PNG is missing. If already posted, it shows the
existing URL + a "Clear link (allow re-post)" button.

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
