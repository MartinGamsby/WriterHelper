# Startup freeze — two distinct causes

`writerhelper.main()` does `ArticlesModel.create()` then `fr().open_last_article()`
(synchronous, BEFORE the window shows), then `webview.start()`.

## 1. Twin-resolution scan (FIXED)
`open_last_article` loads the most-recent FR post, which resolves its EN twin. The old
`_find_by_key` read EVERY sibling `.md` in full on each resolution — ~3s for 400 posts,
seconds on the real ~130-post blog. Now O(1) via the `<key>.md` filename convention +
a header-only fallback scan. Loading all 129 real FR posts ≈ 1.2s total. See
[../file-storage/astro-format.md](../file-storage/astro-format.md).

Also fixed the data that *stranded* startup: one pair (`…-amazon`) had **swapped**
translationKeys (FR carried the EN slug, EN carried the FR slug) so the twin was never
found → `new article en` blanked EN. Resolution now self-heals drifted keys on load.

## 2. Bridge-introspection recursion (FIXED)
Hard freeze/crash on every web-stack startup, logged as:
`[pywebview] Error while processing window.native.AccessibilityObject.Bounds.Empty.
Empty.… : maximum recursion depth exceeded` (+ a follow-on `AllowExternalDrop`
UI-thread COM error).

**Cause = the bridge object, not accessibility.** On page load pywebview's
`inject_pywebview` (`webview/util.py` `get_functions`) walks `dir(window._js_api)` and
**recurses into every PUBLIC non-callable attribute** to expose it to JS. The old
`webapi.Api` held `self.articles` and `self.window` as public attrs, so the walk
descended `api.window` → `window.native` (the .NET WinForms Form) →
`AccessibilityObject.Bounds` → `Rectangle.Empty.Empty…` forever (pythonnet returns a
fresh wrapper each hop, so pywebview's `id()` cycle-guard never trips). `api.articles`
would also crawl the whole model graph.

**Fix:** names starting with `_` are skipped by the walk, so the bridge's data attrs
are private — `Api._articles`, `Api._window` ([../web-ui/bridge.md](bridge.md)). Keep
them underscored and **add no public data attributes to `Api`** (methods are fine —
they're recorded, not recursed). QML never hit this because Qt doesn't introspect the
bridge object.
