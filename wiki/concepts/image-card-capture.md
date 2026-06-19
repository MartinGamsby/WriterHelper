# Image-card capture (html2canvas)

The branded post-image generation. Ported from QML `grabToImage` to `js/capture.js`
using vendored **html2canvas** (`web/vendor/html2canvas.min.js`, v1.4.1). The legacy
QML path still exists ([[legacy-qt-ui]]) but the web path is live.

## The surface

`.card-frame` (id `card-<hl>`) holds an absolutely-positioned `.card-inner` → `.card-scroll`
→ `.card-content` (the `content_md_separators` HTML, [[content-flavors]]). The
`.card-watermark` (a per-`hl` `MartinGamsby.com/<hl>` watermark) and the `.card-page` badge
are **siblings of `.card-inner`, anchored to the frame corner** — so the Margin control
moves only the text/image, never the watermark/badge. Frame width/height come from the W/H
number inputs; the `.card-inner` `inset` (the margin around text + image, old
`contentMargin`, default 9px) from the **Margin** number input; colors from the green/black
checkboxes — all applied locally by `Editor.restyleCard`.

## Output naming (load-bearing contract)

`richTextArea_<slug>_<hl><N>.jpg`, `<N>` 1-indexed, written to CWD. **JPEG** (so it
doubles as the Instagram asset, [[instagram-adapter]]) and **named by the article's
slug** so a capture is tied to the article it was grabbed for — image-mode publishing
resolves the *current* article's slug, so a stale grab from a different post (or an
edited title → new slug) simply isn't found. `capture.js` produces the JPEG data URL
(`toDataURL('image/jpeg', 0.92)`, white bg since JPEG has no alpha) and paginates by
translating `.card-content` up one viewport (`marginTop`) per page; each page is sent to
`webapi.save_capture(hl, page, dataURL)` ([[webapi-bridge]]), which builds the filename
via the single source of truth `publishing.capture_filename(article, page)`. Page 1
(`image_filename(article)`) is what image-mode [[social-publishing]] attaches. Don't
rename without updating producer (`capture.js`/`save_capture`) and consumer
(`publishing`) together.

## Multi-page guard + badge

A card taller than one viewport grabs as **several** files, but only page 1 is used when
publishing a single image — so a multi-page grab is made explicit two ways. (1) While
editing, the `.card-page` badge reads **`1/N`** (not just `1`) whenever `pageCount > 1`,
set in `layoutPages`. (2) `Capture.grab` **awaits `App.confirm`** ([[web-ui]]) before
writing anything when `pageCount > 1` ("Grab N images" / Cancel); Cancel returns early and
saves nothing. Single-page grabs are unchanged (no badge, no prompt). The most common
cause of an unexpected `N`: the **Margin** control shrank the text area enough to overflow
— **Adjust** re-fits because `fitsOnePage` already reflects the current margin.

```mermaid
sequenceDiagram
    User->>Grab: click
    Grab->>capture.js: pageCount = ceil(contentH / viewH)
    alt pageCount > 1
        capture.js->>App.confirm: "Grab N images?"
        App.confirm-->>capture.js: cancel ⇒ return (nothing saved)
    end
    loop each page p
        capture.js->>card-content: marginTop = -(p-1)*viewH
        capture.js->>html2canvas: render(.card-frame)
        html2canvas-->>capture.js: canvas
        capture.js->>webapi: save_capture(hl, p, dataURL)
    end
    capture.js->>layout: restore (centered if single page)
```

## Sizing helpers

| Button | Effect |
|---|---|
| Adjust | Shrink H until content overflows, then bump up one step (32px). |
| Square | H = card width, then `adjustFontSize`. |
| 500x400 | H = width*4/5, then `adjustFontSize`. |
| Portrait | H = width*5/4, then `adjustFontSize`. |
| Landscape | H = width*9/16, then `adjustFontSize` (extra shrink if <300 chars). |

`adjustFontSize` grows the font while content fits one page, then trims; drops a step
for <1000 chars, another for <300. `fitsOnePage` compares `content.offsetHeight` to
`scroll.clientHeight`. Single-page → `.card-scroll.centered` + page badge hidden.

## Card colors (replicates the QML look)

- Green checked → `#24475b` bg, white text.
- Black checked (green off) → black bg, white text.
- Neither → white bg, `#000033` text.

Watermark `#7a9295` (green) else silver; page badge `#ade6b9` (green) / `#000033`
(black) / white.

## See also
- [[content-flavors]] — the `content_md_separators` being captured
- [[social-publishing]] — consumer of the PNG
- [[web-ui]] · [[webapi-bridge]]
