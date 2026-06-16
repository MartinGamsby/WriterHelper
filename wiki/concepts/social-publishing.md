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
- **image** — post the **title** only, attaching `richTextArea_<slug>_<hl>1.jpg` (page 1 of the
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
is on. Publish is blocked while any segment is over the limit. Controls:
**Number posts (1/n)** (default on) and **Attach image to first post** (default on when
an image is available) with a source choice between the **article image** (the post's own
header picture — the default, so a thread shows the real picture not the whole text on a
card) and the **grabbed text card** (`richTextArea_<slug>_<hl>1.jpg`). Each source radio is
disabled until that image exists.

## `prepare_post(article, platform_key) → dict` — NO side effects

Safe to call every time the popup opens. Returns: `text` (`rendering.plain_text`),
`text_length`, `fits` (≤ max_length), `suggested_mode`, `existing_url` (idempotence
guard), `title`, `image_file` (`richTextArea_<slug>_<hl>1.jpg`), `image_exists`,
`image_data_url` (base64 if present), `max_length`, `label`, **`facets_ok`** (≥1 facet —
the mandatory-facets gate, see [[glossary]]), the thread seed `thread_text` /
`thread_count` / `separator` ([[thread-split]]), `author` (a loose identity label for the
preview cards — `martingamsby.com/<hl>`, NOT the real platform handle), and the article
image (`article_image_exists` — a local file is attachable; `article_image_data_url` —
for the preview).

## Link-preview card (Bluesky only)

Bluesky leaves a posted URL as plain text and shows no preview unless the post carries an
`app.bsky.embed.external` card; X/Facebook unfurl links themselves, so this is
**Bluesky-only**. `prepare_post` returns `embed_url` — the candidate
(`publishing.embed_candidate`): a `YouTube`/`YouTube Shorts` [[link-slots]] URL wins
(rendered as a playable video card), else the first URL in the post text. When it's set,
the popup shows an **opt-in-by-default** checkbox **"Add link preview card → \<host\>"** in
**text** and **thread** modes (hidden in image mode — an attached image owns the post's
single embed slot). The card is built at publish time by
`post_bsky.fetch_external_card` ([[bluesky-adapter]]); a fetch failure posts plain rather
than blocking. The preview dock shows a mock card (`▶` for video links).

## `publish(article, platform_key, mode, message, options=None) → {ok, url, error}`

The only method with side effects. `options` carries thread choices + the embed flag
`{"number": bool, "image": "none"|"grabbed"|"article", "embed": bool}` (embed honoured
only for Bluesky, and only without an image on that post).
1. No facet → refused (facets are mandatory).
2. Existing link for the slot → `{ok: False, url: existing, error}`. (Clear it to re-post.)
3. `mode == "thread"` → `_publish_thread`: split `message` on `---`, optionally number,
   reject any over-limit segment, resolve the image source via `_resolve_image` (attaches
   to the first post only; grabbed alt = full text, article alt = title), post the reply
   chain via `poster.post_thread`; the **first** post's URL becomes the slot guard
   (`urls[]` also returned). [[thread-split]]
4. `mode == "image"` → requires the grabbed PNG on disk; posts `message` + that PNG, alt
   text = full article plain text.
5. `mode == "text"` → re-checks `len(message) <= max_length`; posts text only.
6. On success → `set_link(slot, url)` (re-saves the footer, [[link-slots]]) +
   `webbrowser.open(url)`.

## `PLATFORMS` registry

| key | label | link slot | max_length | adapter |
|---|---|---|---|---|
| `bluesky` | Bluesky | `Bluesky` | 300 | `PostBsky(hl)` ([[bluesky-adapter]]) |
| `x` | X / Twitter | `X/Twitter` | 280 | `PostX(hl)` ([[x-adapter]]) |
| `facebook` | Facebook | `Facebook` | 63206 | `PostFB(hl)` ([[facebook-adapter]]) — text/image only |

`make_poster` imports the adapter lazily, so a missing/broken adapter doesn't break
import and tests can monkeypatch the registry.

## The popup (`js/publish.js`)

`Publish.open(hl, platform)` calls `prepare_post`, seeds per-mode drafts (text = full
text, thread = `thread_text`, image = title), and renders a **two-column** modal: the
left column holds the controls — three radio modes (text · thread · image) defaulted to
`suggested_mode`, an **editable** textarea (switching modes swaps the remembered draft),
the live `count / max_length` (text/image) or per-segment readout + Number/Image
checkboxes (thread). Publish is disabled when over the limit, when text is empty, in
image mode when the PNG is missing, or in thread mode when any segment is over. If
already posted, it shows the existing URL + a "Clear link (allow re-post)" button.

## The live preview dock (`renderPreview`)

The right column is a WYSIWYG **"what you'll post"** dock that re-renders on every edit
(`renderPreview(mode, text)` runs inside `validate`). It draws real post **cards**
(avatar + `author` from `prepare_post` + body, `postCard`), approximating the end result
— not platform-accurate:
- **text** → one card with the full body.
- **image** → one card with the title body + the captured PNG (or a "not grabbed yet"
  placeholder). The image lives ONLY here now — it was removed from the controls column.
- **thread** → the segments rendered **exactly as sent** (with the ` (i/n)` counter when
  numbering is on, via `numberedSegments`), stacked as cards joined by a connector line;
  the chosen image (article header or grabbed card, `threadImageData`) attaches to the
  first card when "Attach image to first post" is on.

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
