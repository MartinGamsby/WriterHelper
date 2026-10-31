# WriterHelper entry point: pywebview window hosting the web UI (web/index.html).
# The legacy Qt/QML launcher is preserved as writerhelper_qt.py.
import os
import sys

import webview

from articles import ArticlesModel
from webapi import Api


# ========================================================================================
def main():
    articles = ArticlesModel.create()
    articles.fr().open_last_article()

    api = Api(articles)

    index = os.path.join(os.path.dirname(os.path.realpath(__file__)), "web", "index.html")
    window = webview.create_window("Writer Helper", index, js_api=api,
                                   width=1800, height=1024)
    api.set_window(window)

    webview.start(http_server=True, debug="--debug" in sys.argv)


# ========================================================================================
if __name__ == '__main__':
    main()
