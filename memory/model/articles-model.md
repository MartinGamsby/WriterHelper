# ArticlesModel

`ArticlesModel(QObject)` in `model.py`. Pairs the FR and EN `ArticleModel` instances and owns translation.

## Construction

`Backend.__init__` does:

```python
french  = model.ArticleModel(hl="fr")
english = model.ArticleModel(hl="en")
french.set_ref(english)
english.set_ref(french)
self.articles = model.ArticlesModel(french, english)
french.open_last_article()
```

So at startup: both models exist, are mutually `set_ref`d, and the FR side eagerly loads the most-recent `.md` in its `posts_folder`. Loading FR also loads EN via `change_article`'s reciprocal-ref lookup (see [article-model.md](article-model.md)).

## Slots

- `fr() -> ArticleModel` and `en() -> ArticleModel` — accessors used by QML and by `Backend.article(hl)`.
- `translate(hl: str) -> bool` — see [translation.md](translation.md).

## Reciprocal ref resolution

`ArticleModel.set_ref(other)` stores `self.ref = other`. The `<REF>` placeholder in the Jekyll frontmatter resolves to `ref.website_url + ref.slug` — the URL of the other-language version of this article.

`change_article` uses the same pairing for *loading*: when an existing post has `ref: https://martingamsby.github.io/foo` in frontmatter, the model strips the `ref.website_url` prefix to get the slug, prepends `<date>-`, and looks for the matching file in `ref.posts_folder`. If found, loads it via `ref.change_article(..., change_ref=False)`; otherwise calls `ref.new_article()`. The `change_ref=False` guard prevents infinite recursion.

## See also
- [article-model.md](article-model.md)
- [translation.md](translation.md)
