# pywebview JS bridge: everything the web UI calls lives here.
# JS calls window.pywebview.api.<method>(...) and gets JSON back.
import base64
import webbrowser

import rendering
import publishing
from articles import ArticlesModel

# Link slots shown in the meta panel, in footer order. "publish" marks slots
# with a platform adapter (clicking their button opens the confirmation popup).
LINK_SLOTS = [
    {"name": "Medium", "hls": ["fr"]},
    {"name": "Typeshare", "hls": ["en"]},
    {"name": "X/Twitter", "hls": ["fr", "en"], "publish": "x"},
    {"name": "LinkedIn", "hls": ["en"]},
    {"name": "Facebook", "hls": ["fr"]},
    {"name": "Bluesky", "hls": ["fr", "en"], "publish": "bluesky"},
    {"name": "YouTube", "hls": ["fr", "en"]},
    {"name": "YouTube Shorts", "hls": ["fr", "en"]},
    {"name": "Source", "hls": ["fr", "en"]},
]


# ========================================================================================
class Api:

    # ====================================================================================
    def __init__(self, articles: ArticlesModel):
        self.articles = articles
        self.window = None  # set after webview.create_window

    def set_window(self, window):
        self.window = window

    def _article(self, hl):
        return self.articles.get(hl)

    # ====================================================================================
    def get_state(self, hl):
        a = self._article(hl)
        slots = []
        for slot in LINK_SLOTS:
            if hl in slot["hls"]:
                slots.append({"name": slot["name"],
                              "url": a.get_link(slot["name"]),
                              "publish": slot.get("publish", "")})
        slots.append({"name": a.get_based_on_text(),
                      "url": a.get_link(a.get_based_on_text()), "publish": ""})
        return {
            "hl": hl,
            "title": a.title,
            "content": a.content,
            "date": a.date,
            "tags": a.tags,
            "excerpt_image": a.excerpt_image,
            "excerpt_image_local": rendering.excerpt_image_local(a) if a.excerpt_image else "",
            "posts_folder": a.get_posts_folder(),
            "website_url": a.get_website_url(),
            "slug": a.get_slug(),
            "green": a.green,
            "black": a.black,
            "title_color": rendering.title_color(a),
            "length_short": "Medium" if a.medium else ("Mini" if a.mini else "Short"),
            "links": slots,
            "content_md": a.content_md(),
            "content_md_separators": a.content_md_separators(),
            "content_md_separators_br": a.content_md_separators_br(),
            "content_short": a.content_short(),
            "watermark": "linktr.ee/Gamsby" if hl == "en" else "linktr.ee/MGamsby",
        }

    # ====================================================================================
    def set_field(self, hl, field, value):
        a = self._article(hl)
        setters = {
            "title": a.set_title,
            "content": a.set_content,
            "date": a.set_date,
            "tags": a.set_tags,
            "excerpt_image": a.set_excerpt_img,
            "posts_folder": a.set_posts_folder,
            "website_url": a.set_website_url,
            "green": a.set_green,
            "black": a.set_black,
        }
        setters[field](value)
        return True

    def set_link(self, hl, name, url):
        self._article(hl).set_link(name, url)
        return True

    # ====================================================================================
    def new_article(self, hl, copy_current=False):
        self._article(hl).new_article(copy_current=copy_current)
        return True

    def new_both_articles(self, hl, copy_current=False):
        self._article(hl).new_both_articles(copy_current=copy_current)
        return True

    def open_article(self, hl):
        a = self._article(hl)
        import webview
        result = self.window.create_file_dialog(
            webview.OPEN_DIALOG, directory=a.get_posts_folder(),
            file_types=("Markdown (*.md)",))
        if result:
            file_name = result[0] if isinstance(result, (list, tuple)) else result
            a.load_file(file_name)
            return True
        return False

    def open_prev_article(self, hl):
        self._article(hl).open_prev_article()
        return True

    def open_next_article(self, hl):
        self._article(hl).open_next_article()
        return True

    def translate(self, hl):
        return self.articles.translate(hl)

    # ====================================================================================
    # Publishing: popup data, then explicit user-confirmed send.
    def prepare_post(self, hl, platform):
        return publishing.prepare_post(self._article(hl), platform)

    def publish(self, hl, platform, mode, message):
        return publishing.publish(self._article(hl), platform, mode, message)

    def clear_link(self, hl, platform):
        name = publishing.PLATFORMS[platform].link_name
        self._article(hl).set_link(name, "")
        return True

    # ====================================================================================
    def save_capture(self, hl, page, data_url):
        """Persist one captured card page as richTextArea_<hl><page>.png (CWD,
        same contract as the old QML grabToImage output)."""
        encoded = data_url.split(",", 1)[1]
        filename = f"richTextArea_{hl}{page}.png"
        with open(filename, "wb") as f:
            f.write(base64.b64decode(encoded))
        print("Saved", filename)
        return filename

    # ====================================================================================
    def open_url(self, url):
        webbrowser.open(url)
        return True
