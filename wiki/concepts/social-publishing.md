# Social publishing — two-phase, behind a popup

Publishing to a social platform is **two-phase**: a side-effect-free `prepare_post`
that fills a confirmation popup, then a `publish` that actually sends only what the user
confirmed. Code: `publishing.py` ([[publishing]]) + `js/publish*.js`. Each platform is
reached by one of two **transports**: `api` (a native adapter posts immediately — always
Bluesky) or `browser` (the post is **queued for Claude in Chrome** and the URL arrives
later — the default for everything else). See [[browser-hook]].

## The three modes (text · thread · image)

A post is sent one of three ways, chosen by radio in the popup:

- **text** — post the rendered plain text as one post.
- **thread** — split the plain text into a reply chain of posts that each fit the limit
  ([[thread-split]]); the author can **edit where it splits** (see below).
- **image** — post the **title** only, attaching an image. The attachment source is a
  radio choice between the **grabbed text card** (`richTextArea_<slug>_<hl>1.jpg`, page 1
  of the captured card, [[image-card-capture]] — the default) and the **article image**
  (the post's own header picture). Same article-vs-grabbed pair offered for a thread's
  first-post image; each radio is disabled until that image exists.

The suggestion hinges on the **rendered plain-text length** vs the platform's char limit
(not the `mini`/`medium` UI [[glossary]] length category): fits → `suggested_mode="text"`;
doesn't fit → `suggested_mode="thread"`. `prepare_post` computes this; the popup defaults
to it but the user can override to any mode.

## Media requirements (`Platform.media`) — what each platform *needs*

Beyond char limits, a platform constrains which modes are even valid. Each `Platform`
carries `media`: `"any"` (text or image — Bluesky, X, Facebook, LinkedIn, Threads,
Medium), `"image"` (an image is **mandatory** — Instagram, Pinterest, TikTok photo
posts), or `"video"` (no platform today; the [[video-posts]] roadmap). `prepare_post`
returns it, and the popup acts on it:
- **`"image"`** → only the **Title + image** mode is offered (Text/Thread radios omitted),
  `suggested_mode` is forced to `image`, and the go button stays disabled until an image
  exists.
- **`"video"`** → the popup shows a **gate** (`renderUnsupportedVideo`) instead of a
  composer: WriterHelper authors no video yet.

`publish()` re-checks both server-side (a `video` platform is refused; an `image` platform
rejects a non-image mode). Instagram **over the API** keeps its own two-step panel
([[instagram-adapter]]); over the browser it's an ordinary image post.

## Editable split points (Thread mode)

`prepare_post` returns `thread_text`: the auto-split segments joined by `---` lines
([[thread-split]] `join_for_edit`). The popup loads that into the textarea; the author
moves/adds/removes `---` lines to control the breaks. A live per-segment readout shows
`#i len/max` (red when over), accounting for the projected ` (i/n)` counter when numbering
is on. Publish is blocked while any segment is over the limit. Controls:
**Number posts (1/n)** (default off) and **Attach image to first post** (default on when
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

## `publish(article, platform_key, mode, message, options=None) → dict`

The only method with side effects. `options` carries thread choices, the image source,
and the embed flag `{"number": bool, "image": "none"|"grabbed"|"article", "embed": bool}`
(`image` is read in both thread and image modes; embed honoured only for Bluesky over the
API, and only without an image on that post).
1. No facet → refused (facets are mandatory).
2. Existing link for the slot → `{ok: False, url: existing, error}`. (Clear it to re-post.)
3. Browser transport with a still-pending job for this article+platform → refused.
4. `media == "video"` → refused; Instagram-over-API → its two-step path; image-required
   platform + non-image mode → refused.
5. `_plan` turns the confirmed input into `(posts, image, alt_text)`, transport-agnostic:
   - **thread** → refused where `supports_thread` is False; split `message` on `---`,
     optionally number, reject any over-limit segment; image source default `"none"`.
     [[thread-split]]
   - **image** → `[message]` + image source default `"grabbed"`.
   - **text** → `[message]`, refused when blank.
   - non-thread `message` over `max_length` → refused. `_resolve_image` resolves the
     source; alt = full plain text for the grabbed card, else the title (text mode: the
     message).
6. **browser** → `browser_jobs.create(...)` + `run_hook` → `{ok, queued: True, url: "",
   job, hook}`; the link is written later by `apply_results` ([[browser-hook]]).
   **api** → `post_thread` / `post`; the **first** URL becomes the slot guard
   (`set_link`, re-saves the footer, [[link-slots]]) + `webbrowser.open`; thread results
   also carry `urls[]`.

## `PLATFORMS` registry

Lives in `platforms.py` (re-exported by `publishing`); the table with transports is in
[[publishing]] and [[browser-hook]]. `supports_thread` is True for Bluesky, X and
Threads (native `post_thread`, or the browser composer's "add post"); False elsewhere,
so `prepare_post` suggests **Image** rather than **Thread** for a too-long post, and
`js/publish.js` **omits the Thread radio** and the hint reads "post as image".

## The popup (`js/publish*.js`)

`Publish.open(hl, platform)` calls `prepare_post`. A `pending_job` short-circuits to the
browser job's status panel (`publish-browser.js`); Instagram-over-API to its two-step
panel (`publish-ig.js`). Otherwise it seeds per-mode drafts (text = full
text, thread = `thread_text`, image = title), and renders a **two-column** modal: the
left column holds the controls — three radio modes (text · thread · image) defaulted to
`suggested_mode`, an **editable** textarea (switching modes swaps the remembered draft),
the live `count / max_length` (text/image) or per-segment readout + Number/Image
checkboxes (thread), plus an **Image source** radio pair (grabbed card / article image)
in image mode. Publish is disabled when over the limit, when text is empty, in image mode
when the selected image source is missing, or in thread mode when any segment is over. If
already posted, it shows the existing URL + a "Clear link (allow re-post)" button. For a
browser-routed platform the go button reads **Queue for Claude in Chrome** with a 🌐 note,
and a successful queue swaps the modal to the job panel (copyable `/chrome-post <id>`,
3 s poll → "Posted ✓", failure reason + "Edit & re-queue", Cancel job, Run hook again).

## The live preview dock (`renderPreview`)

The right column is a WYSIWYG **"what you'll post"** dock that re-renders on every edit
(`renderPreview(mode, text)` runs inside `validate`). It draws real post **cards**
(avatar + `author` from `prepare_post` + body, `postCard`), approximating the end result
— not platform-accurate:
- **text** → one card with the full body.
- **image** → one card with the title body + the chosen image (grabbed card or article
  header, via the same `imageSource`/`imageSourceData` helpers, or a "no image" placeholder
  when the selected source doesn't exist yet).
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
- [[browser-hook]] · [[publishing]] · [[post-base]] · [[bluesky-adapter]] · [[x-adapter]]
- [[image-card-capture]] — produces the PNG image mode attaches
- [[link-slots]] — where the returned URL is stored
