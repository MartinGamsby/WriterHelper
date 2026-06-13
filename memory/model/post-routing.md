# Social-Post Routing

> **Updated:** routing now lives in `publishing.py` as the two-phase `prepare_post` / `publish` pair, behind a confirmation popup. See [../posting/popup-flow.md](../posting/popup-flow.md) for the live design. The text-vs-image logic below still describes the *decision*, which is preserved (`prepare_post` computes `suggested_mode`; the user may override it in the popup). The old single-shot `ArticleModel.post` remains only in legacy `model.py`.

The decision: what to push to a social platform and what URL to record.

## Signature & flow

```python
def post(self, name, poster, max_length):
    if self.get_link(name):              # already posted? skip
        print("Link already exists!")
        return
    soup = BeautifulSoup(self.content_md_separators_br(add_tags=False), "html.parser")
    text = soup.get_text()
    if len(text) <= max_length:
        url = poster.post(msg=text, image_local_url=None, alt_text=text)
    else:
        url = poster.post(msg=self.title, image_local_url=f"richTextArea_{self.hl}1.png", alt_text=text)
    self.set_link(name, url)
    QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
    return url
```

Three observable effects:
1. The platform's adapter posts.
2. The returned URL is stored in `links` under `name`, which causes `on_updated` → `ContentFile.create_file` to rewrite the `.md` with an updated footer.
3. The browser opens the new post.

## Idempotence guard

If `links` already contains a non-empty URL for `name`, the helper returns early with `"Link already exists!"`. This means: to re-post, manually clear the link in the UI (TextField in `ArticleMeta.qml`) first.

## Text-vs-image decision

The fallback hinges on **plain-text length** (HTML stripped via BeautifulSoup) vs the platform's `max_length`:
- Fits: post `text` only, no image.
- Doesn't fit: post `self.title` only, with `richTextArea_<hl>1.png` (page 1 of the captured surface) as the image.

⚠️ This is decoupled from the `mini`/`medium` length categories used in the UI label. Those categorize *content length* (mini < 280, medium > 2000); routing uses the platform limit applied to the *rendered plain text* (which includes the title + content + decorations + body text). It happens that mini articles almost always go text-only and medium ones almost always go image, but the decision is the post-time string length, not the category flag.

## Wired slots

| Slot | Platform | max_length |
|---|---|---|
| `post_bluesky()` | `PostBsky(self.hl)` | 300 |
| `post_x()` | `PostX(self.hl)` | 280 |

These are invoked from `ArticleMeta.qml` Label `onLinkActivated` handlers (clicking the platform link label).

## Length category flags

- `mini = len(content) < 280`
- `medium = len(content) > 2000`
- else neither — UI calls this `short` / `Court`.

These are recomputed in `set_content` and `determine_length_category`. They drive: the UI label, the `<CATEGORIES>` array in frontmatter (`Length: Mini|Short|Medium` / `Longueur: Mini|Court|Moyen`), and nothing in the social-post path.

## See also
- [article-model.md](article-model.md)
- [rendering.md](rendering.md)
- [../posting/summary.md](../posting/summary.md)
- [../ui/image-capture.md](../ui/image-capture.md) — produces the PNG used by the image fallback
