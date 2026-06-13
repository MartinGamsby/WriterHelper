# Frontend — Columns & Wiring

Two builders run per language at boot (`App.boot` → `Meta.build(hl)`, `Editor.build(hl)`), injecting HTML into the four `<section>` placeholders. Both expose `apply(hl, state)` to render from `get_state`.

## Content column (`editor.js`)
Header (length label, "<hl> Article", char/word counter), posts-folder + website-URL inputs, title input + slug line, date-override checkbox+input, the content `<textarea>`, a controls row (Font / G / B / W / H / Center), the buttons row (Grab/Adjust/Square/Portrait/Landscape/500x400), short-content preview, the `.card-frame` capture surface, then read-only previews of `content_md_separators_br` and `content_md` (the raw Jekyll file).

Wiring: every `[data-field]` input debounce-saves via `App.setField` on `input` and immediately on `change`. Green/Black checkboxes call `set_field`. Font/W/H/Center are **local only** — they call `Editor.restyleCard` without a backend round-trip (card geometry isn't persisted).

## Meta column (`meta.js`)
Button grid (New / Translate / Open / Make V2 / Open Prev / Open Next / New both articles — each awaits the bridge then `App.refreshAll`), the Image field + preview `<img>`, the Links grid, the Tags field.

Link slots render one `.link-row` each. Slots with `publish` (`x`/`bluesky`) get a `<button>` that opens `Publish.open(hl, platform)`; others get a plain label. The URL `<input>` debounce-saves via `App.setLink`. Rows are created once and updated in place; a row's input is not overwritten while focused.

## Shared (`app.js`)
- `debounce(fn, ms)`, `setValue(id, v)` (skips focused inputs), `toast(msg)`.
- `refresh(hl)` / `refreshAll()` / `setField` / `setLink` — all re-fetch state after mutating.
- Boot also wires FR/EN visibility checkboxes, the 1s fr-CA clock, and overlay-click-to-close for the modal.

## Theme (`style.css`)
Green identity (`--green-strip #2e7d32`, `--green-dark #24475b`, `--accent #ade6b9`). Columns are fixed-width flex items in a horizontally-scrolling row; `.hidden` removes them.

## See also
- [summary.md](summary.md)
- [bridge.md](bridge.md)
- [capture.md](capture.md)
