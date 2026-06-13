# ArticlesModel

Pure-Python `ArticlesModel` in `articles.py` (active web stack). Pairs the FR and EN
`ArticleModel` instances and owns translation. (A legacy Qt twin exists in `model.py`.)

## Construction

`ArticlesModel.create(config_dir=".")`:

```python
french  = ArticleModel(hl="fr", config_dir=config_dir)
english = ArticleModel(hl="en", config_dir=config_dir)
french.set_ref(english)
english.set_ref(french)
return ArticlesModel(french, english)
```

Both models exist for the whole session, mutually `set_ref`d. The entry point
(`writerhelper.py`) builds them and may eagerly load the most-recent `.md`. Loading
one side also loads its twin (see twin resolution below).

## Methods

- `fr()`, `en()`, `get(hl)` — accessors used by `webapi.Api`.
- `translate(hl)` — see [translation.md](translation.md).

## Pairing / twin resolution

`ArticleModel.set_ref(other)` stores `self.ref = other`. Twins now pair by
`translationKey`, not by URL:

- **Astro (current):** loading a file reads its `translationKey` and scans the other
  language's folder for a file with the same `translationKey:` line, then loads it via
  `ref.change_article(..., change_ref=False)`; else `ref.new_article()`.
- **Jekyll (legacy load):** the old behavior survives — strip `ref.website_url` from
  the frontmatter `ref:` URL to get the slug, prepend `<date>-`, find that file in
  `ref.posts_folder`.

Both live in `serializers.py`; the `change_ref=False` guard prevents infinite
recursion. See [../file-storage/astro-format.md](../file-storage/astro-format.md).

## See also
- [article-model.md](article-model.md)
- [translation.md](translation.md)
