# Translation

`ArticlesModel.translate(hl: str) -> bool` in `model.py`.

## Direction

The `hl` argument is the **source** language. Destination is the *other* one.

```python
if hl == "en":
    src = self.en(); dst = self.fr(); dst_hl = "fr"
else:
    src = self.fr(); dst = self.en(); dst_hl = "en"
```

UI-wise: the "Translate" button in `ArticleMeta.qml` calls `root.backend.translate(menu.hl)` where `menu.hl` is the language of the *meta* column the button is in. So clicking Translate on the FR meta column translates **from** FR **to** EN. Mental model: "translate this side outward."

## Empty-destination guard

```python
if dst.content:
    print("SOURCE ALREADY HAS CONTENT!!")
    return
```

If the destination already has content, the call aborts (no overwrite). To re-translate, clear the destination first.

## What gets translated

Via `deep_translator.GoogleTranslator(source=hl, target=dst_hl)`:
- `title`
- `content`
- `tags`

Also copied verbatim (no translation):
- `excerpt_image`
- `date`

`links` are NOT touched.

## See also
- [articles-model.md](articles-model.md)
- [article-model.md](article-model.md)
