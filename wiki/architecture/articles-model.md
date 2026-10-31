# ArticlesModel (`articles.py`)

Pure-Python `ArticlesModel` (active web stack). Pairs the FR and EN [[article-model]]
instances and owns translation. A legacy Qt twin exists in `model.py`.

## Construction

`ArticlesModel.create(config_dir=".")`:

```python
french  = ArticleModel(hl="fr", config_dir=config_dir)
english = ArticleModel(hl="en", config_dir=config_dir)
french.set_ref(english)
english.set_ref(french)
return ArticlesModel(french, english)
```

Both models live for the whole session, mutually `set_ref`d. The entry point
(`writerhelper.py`) builds them and eagerly loads the most-recent FR `.md`
(`fr().open_last_article()`) **before the window shows** — loading one side also loads
its twin. (That synchronous startup load is why twin resolution must be fast — see the
O(1) lookup in [[bilingual-pairing]] / [[astro-format]].)

## Methods

- `fr()`, `en()`, `get(hl)` — accessors used by [[webapi-bridge]].
- `translate(hl)` — one-way, fills only an empty destination. See [[machine-translation]].

## Pairing / twin resolution

`set_ref(other)` stores `self.ref = other`. Twins pair by `translationKey`, resolved in
[[serializers]] (`change_ref=False` guards recursion). Full rules: [[bilingual-pairing]].

## See also
- [[article-model]] · [[machine-translation]] · [[model-layer]]
