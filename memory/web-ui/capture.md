# Image Capture (html2canvas)

The branded post-image generation, ported from QML `grabToImage` to `js/capture.js` using vendored **html2canvas** (`web/vendor/html2canvas.min.js`, v1.4.1).

## The surface
`.card-frame` (id `card-<hl>`) holds an absolutely-positioned `.card-inner` (9px margin = old `contentMargin`) containing `.card-scroll` → `.card-content` (the `content_md_separators` HTML), a `.card-watermark` (`MartinGamsby.com/en` EN, `MartinGamsby.com/fr` FR), and a `.card-page` badge. Frame width/height come from the W/H number inputs; colors from green/black checkboxes via `Editor.restyleCard`.

## Output naming (unchanged contract)
`richTextArea_<hl><N>.png`, `<N>` 1-indexed. `capture.js` paginates by translating `.card-content` up one viewport (`marginTop`) per page and re-capturing; each page is sent to `webapi.save_capture(hl, page, dataURL)`. Page 1 (`richTextArea_<hl>1.png`) is what the publish image mode attaches.

```mermaid
sequenceDiagram
    User->>Grab: click
    Grab->>capture.js: pageCount = ceil(contentH / viewH)
    loop each page p
        capture.js->>card-content: marginTop = -(p-1)*viewH
        capture.js->>html2canvas: render(.card-frame)
        html2canvas-->>capture.js: canvas
        capture.js->>webapi: save_capture(hl, p, dataURL)
    end
    capture.js->>layout: restore (centered if single page)
```

## Sizing helpers (ported)
| Button | Effect |
|---|---|
| Adjust | Shrink H until content overflows, then bump up one step (32px). |
| Square | H = card width, then `adjustFontSize`. |
| 500x400 | H = width*4/5, then `adjustFontSize`. |
| Portrait | H = width*5/4, then `adjustFontSize`. |
| Landscape | H = width*9/16, then `adjustFontSize` (extra shrink if <300 chars). |

`adjustFontSize` grows the font while content fits one page, then trims; drops a step for <1000 chars, another for <300. `fitsOnePage` compares `content.offsetHeight` to `scroll.clientHeight`. Single-page → `.card-scroll.centered` (vertical center) and page badge hidden.

## Card colors (replicates QML)
- Green checked → `#24475b` bg, white text.
- Black checked (green off) → black bg, white text.
- Neither → white bg, `#000033` text.
Watermark `#7a9295` (green) else silver; page badge `#ade6b9` (green) / `#000033` (black) / white.

## See also
- [summary.md](summary.md)
- [../model/rendering.md](../model/rendering.md) — the `content_md_separators` being captured
- [../posting/popup-flow.md](../posting/popup-flow.md) — consumer of the PNG
