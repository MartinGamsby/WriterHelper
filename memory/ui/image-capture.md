# Image Capture (`grabToImage`)

The branded post-image generation lives entirely in QML (`ArticleContent.qml`). The `richTextArea` Rectangle is rendered with the styled content (`p_content_md_separators`) and snapshotted to PNG. The output PNGs are then consumed by the social-post fallback when text is too long.

## Output naming

`outputName + outputId + ".png"` where:
- `outputName = "richTextArea_" + menu.hl` (so `richTextArea_fr` or `richTextArea_en`)
- `outputId` starts at 0, incremented inside `grabCallback` so saved files are `..._1.png`, `..._2.png`, ...

Resulting paths are relative to CWD (= the project root when run via `writerhelper.py`).

⚠️ The social-post fallback in `ArticleModel.post` reads `richTextArea_<hl>1.png` (page 1) specifically. See [../model/post-routing.md](../model/post-routing.md).

## Capture flow

```mermaid
sequenceDiagram
    User->>Grab Button: click
    Grab Button->>render(): outputId=0; contentY=0
    render()->>richTextArea: grabToImage(grabCallback)
    richTextArea-->>grabCallback: result
    grabCallback->>Disk: result.saveToFile("richTextArea_<hl>1.png")
    grabCallback->>contentFlickable: contentY += page-height
    alt not atYEnd
        grabCallback->>richTextArea: grabToImage(grabCallback) again
    else atYEnd
        grabCallback->>columnState: outputId = 0
    end
```

The callback paginates by advancing `contentFlickable.contentY` one screen at a time and re-grabbing until `atYEnd`. Each iteration writes the next-numbered PNG. Margins (`contentBg.anchors.topMargin/bottomMargin`) are toggled to `-3` between pages so split content doesn't show a gap, then restored to `contentMargin` on the final page.

## Sizing helpers

Buttons that pre-set `sbHeight` and call `adjustFontSize()`:

| Button | Effect |
|---|---|
| `Adjust` | Shrinks `sbHeight` until content just fits one page (binary search down then bump up by one step). |
| `Square` | `sbHeight = richTextArea.width`, then `adjustFontSize`. |
| `500x400` | `sbHeight = width*4/5`, then `adjustFontSize`. |
| `Portrait` | `sbHeight = width*5/4`, then `adjustFontSize`. |
| `Landscape` | `sbHeight = width*9/16`, then `adjustFontSize` (with extra font shrink if `< 300` chars). |

`adjustFontSize()` grows the font as long as content still fits one page, then trims back. Drops a step for content `< 1000` chars; another step for `< 300`. (Smaller content → smaller font, intentionally — so the layout doesn't look cartoonishly large for a short post.)

## Visual style

The `richTextArea` background color depends on the green/black checkboxes:
- Green (`cbGreen.checked`) → `#24475b` background, white text.
- Black (`cbBlack.checked`, green off) → black background, white text.
- Neither → white background, `#000033` text.

Plus per-`hl` watermark text (`linktr.ee/Gamsby` for EN, `linktr.ee/MGamsby` for FR) and a page-number indicator visible only when content overflows one page.

## See also
- [qml-tree.md](qml-tree.md)
- [../model/rendering.md](../model/rendering.md) — the `content_md_separators` flavor being captured
- [../model/post-routing.md](../model/post-routing.md) — the consumer of the PNG output
