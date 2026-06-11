# WriterHelper — Summary

Personal bilingual (FR/EN) blog-authoring desktop app for [martingamsby.github.io](https://martingamsby.github.io/) (a Jekyll site).
Pairs FR + EN articles side-by-side, auto-saves Jekyll posts on every edit, renders branded image cards from rich-text content via QML `grabToImage`, and posts to BlueSky and X (text if it fits the platform limit, else title + the generated PNG).

Stack: Python 3 + PySide6 (QtCore/QtWidgets/QtQml/QtGui) + QtQuick/QML + atproto, tweepy, deep_translator, requests, markdown, beautifulsoup4, pyyaml, unidecode.
Packaged with PyInstaller (`writerhelper.spec`). Single-user, Windows.

```mermaid
graph TD
    EP[writerhelper.py] --> BE[backend.py: Backend QObject]
    EP --> QML[ui/qml/main.qml]
    BE --> ASM[model.py: ArticlesModel]
    ASM --> FR[ArticleModel hl=fr]
    ASM --> EN[ArticleModel hl=en]
    FR <-. set_ref .-> EN
    FR -- updated Signal --> CF[filemanager.ContentFile]
    EN -- updated Signal --> CF
    CF --> POSTS[(YYYY-MM-DD-slug.md)]
    FR --> PB[post_bsky.PostBsky]
    FR --> PX[post_x.PostX]
    EN --> PB
    EN --> PX
    QML --> AC[ArticleContent.qml]
    QML --> AMETA[ArticleMeta.qml]
    QML --> CL[CheckList.qml]
    AC -- grabToImage --> PNG[(richTextArea_hl_N.png)]
    PB -. fallback uses .-> PNG
    PX -. fallback uses .-> PNG
```

Two `ArticleModel` instances live for the whole session — one `hl="fr"`, one `hl="en"` — paired by `set_ref` so each knows the other's website URL for the Jekyll `ref:` field.
The UI (`main.qml`) shows up to four columns: FR meta | FR content | EN content | EN meta. The FR/EN column visibility is toggled by checkboxes in the title bar.

## See also
- [terminology.md](terminology.md)
- [practices.md](practices.md)
- [memory-map.md](memory-map.md)
