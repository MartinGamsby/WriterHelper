# Machine translation (fill the empty twin)

`ArticlesModel.translate(hl)` fills one language's article from the other using
`deep_translator.GoogleTranslator`. It is **one-way** and only fills an **empty**
destination.

## Direction

The `hl` argument is the **source** language; the destination is the *other* one.
Mental model: "translate this side outward."

```python
if hl == "en":
    src = self.en(); dst = self.fr(); dst_hl = "fr"
else:
    src = self.fr(); dst = self.en(); dst_hl = "en"
```

In the UI, the "Translate" button sits in a meta column tied to one `hl`; clicking it
translates *from* that side *to* the other.

## Empty-destination guard

```python
if dst.content:
    print("SOURCE ALREADY HAS CONTENT!!")
    return
```

If the destination already has content, the call aborts — no overwrite. To
re-translate, clear the destination first. This is an [[invariants-and-traps]]
invariant.

## What gets translated

Via `GoogleTranslator(source=hl, target=dst_hl)`: `title`, `content`, `tags`.
Copied verbatim (no translation): `excerpt_image`, `date`. **`links` are not touched.**

Note: French content is Quebec French with Martin's colloquial voice — a bad machine
translation is expected to be hand-proofed (the legacy [[legacy-qt-ui]] checklist
spells this out).

## See also
- [[articles-model]] — where `translate` lives
- [[bilingual-pairing]] — the twin relationship this fills
