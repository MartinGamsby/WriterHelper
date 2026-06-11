# CheckList (manual workflow)

`CheckList.qml` is a static UI sidebar — the operator's mental checklist for publishing an article. Not data-bound, not persisted; checks are session-only and exist purely as a visual reminder.

## Steps (in display order)

1. Write the content
2. Start an image generation (or find it)
3. Proofread
4. Translate (and proofread in French if the translation is bad)
5. Find/write tags
6. Share to **Typeshare** (label is a clickable link → opens browser)
   - COPY LINK of Typeshare here
   - COPY IMAGE URL of Typeshare here
7. Share to **X/Twitter** (eventually/if applicable: adapt for X)
   - COPY LINK of X here
8. Share to **Bluesky**
   - COPY LINK of Bluesky here
9. Share to **Facebook**
   - Share in Facebook if relevant
   - COPY LINK of Facebook here
10. (Medium step is commented out in source.)
11. GITHUB: Upload the article!

## What's automated vs manual

| Step | Automated path |
|---|---|
| 4 (Translate) | "Translate" button in `ArticleMeta` → `Backend.translate(hl)` |
| 7 (X) | Clicking the `X/Twitter` link label in `ArticleMeta` → `ArticleModel.post_x()` |
| 8 (Bluesky) | Clicking the `Bluesky` link label in `ArticleMeta` → `ArticleModel.post_bluesky()` |
| All others | Manual |

Step 11 (GitHub upload) is fully manual: the saved `.md` lands in the configured Jekyll `_posts` folder, and the operator pushes via their git client. WriterHelper does not touch git.

## See also
- [qml-tree.md](qml-tree.md)
- [../model/post-routing.md](../model/post-routing.md)
- [../posting/summary.md](../posting/summary.md)
