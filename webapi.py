# pywebview JS bridge: everything the web UI calls lives here.
# JS calls window.pywebview.api.<method>(...) and gets JSON back.
import base64
import webbrowser

import localize
import rendering
import publishing
import serializers
from articles import ArticlesModel

# Link slots shown in the meta panel, in footer order. "publish" marks slots
# with a platform adapter (clicking their button opens the confirmation popup).
LINK_SLOTS = [
    {"name": "Medium", "hls": ["fr"]},
    {"name": "Typeshare", "hls": ["en"]},
    {"name": "X/Twitter", "hls": ["fr", "en"], "publish": "x"},
    {"name": "LinkedIn", "hls": ["en"]},
    {"name": "Facebook", "hls": ["fr", "en"], "publish": "facebook"},
    {"name": "Bluesky", "hls": ["fr", "en"], "publish": "bluesky"},
    {"name": "YouTube", "hls": ["fr", "en"]},
    {"name": "YouTube Shorts", "hls": ["fr", "en"]},
    {"name": "Source", "hls": ["fr", "en"]},
]


# ========================================================================================
class Api:

    # ====================================================================================
    # NOTE: these MUST stay underscore-prefixed. When pywebview injects the JS bridge it
    # walks dir(api) and recurses into every PUBLIC non-callable attribute to expose it
    # (webview/util.py get_functions). A public `self.window` would lead it into
    # window.native (the .NET WinForms Form) → AccessibilityObject.Bounds →
    # Rectangle.Empty.Empty… → infinite recursion / UI-thread COM errors at startup;
    # a public `self.articles` would make it crawl the whole model graph. Names starting
    # with `_` are skipped, so keep these private. Do NOT add public data attributes here.
    def __init__(self, articles: ArticlesModel):
        self._articles = articles
        self._window = None  # set after webview.create_window

    def set_window(self, window):
        self._window = window

    def _article(self, hl):
        return self._articles.get(hl)

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
            "post_url": a.get_post_url(),
            "facets": a.facets,
            "all_facets": serializers.FACETS,
            "draft": a.draft,
            "translation_key": a.get_translation_key(),
            "green": a.green,
            "black": a.black,
            "title_color": rendering.title_color(a),
            "length_short": "Medium" if a.medium else ("Mini" if a.mini else "Short"),
            "links": slots,
            "content_md": a.content_md(),
            "content_md_separators": a.content_md_separators(),
            "content_md_separators_br": a.content_md_separators_br(),
            "content_short": a.content_short(),
            "watermark": "MartinGamsby.com/en" if hl == "en" else "MartinGamsby.com/fr",
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
            "facets": a.set_facets,
            "draft": a.set_draft,
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
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG, directory=a.get_posts_folder(),
            file_types=("Markdown (*.md)",))
        if result:
            file_name = result[0] if isinstance(result, (list, tuple)) else result
            a.load_file(file_name)
            return True
        return False

    def open_image(self, hl):
        """Pick a local image via the native dialog and set it as the excerpt
        image. It's handed to the model as a data: URL, so it flows through the
        same self-hosting hook as a pasted remote URL (download/decode → webp
        derivatives → frontmatter rewrite). Returns False if the user cancels.
        Drag-drop takes the other door: the JS reads the file and calls
        set_field('excerpt_image', <data url>) directly."""
        import webview
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=("Image files (*.png;*.jpg;*.jpeg;*.webp;*.gif;*.bmp)",
                        "All files (*.*)"))
        if not result:
            return False
        path = result[0] if isinstance(result, (list, tuple)) else result
        self._article(hl).set_excerpt_img(localize.file_to_data_url(path))
        return True

    def open_prev_article(self, hl):
        self._article(hl).open_prev_article()
        return True

    def open_next_article(self, hl):
        self._article(hl).open_next_article()
        return True

    def translate(self, hl):
        return self._articles.translate(hl)

    # ====================================================================================
    # Publishing: popup data, then explicit user-confirmed send.
    def prepare_post(self, hl, platform):
        return publishing.prepare_post(self._article(hl), platform)

    def publish(self, hl, platform, mode, message, options=None):
        return publishing.publish(self._article(hl), platform, mode, message, options)

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
