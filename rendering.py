# Pure rendering helpers for ArticleModel: the five content_md flavors,
# footer, categories, and local-image embedding. No Qt, no UI.
import os
import re
from pathlib import Path

import markdown
from bs4 import BeautifulSoup
from unidecode import unidecode

import localize


# ========================================================================================
def load_templates():
    base = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')

    def read(name):
        with open(os.path.join(base, name), mode="r", encoding="utf-8") as f:
            return f.read()

    return {
        "post": read('post.md'),
        "content": read('post_content.md'),
        "content_only": read('post_content_only.md'),
        "title_only": read('post_title_only.md'),
    }


# ========================================================================================
def title_color(article):
    if article.green:
        return "#ade6b9"
    if article.black:
        return "white"
    return "black"


# ========================================================================================
def templated(article, template) -> str:
    if os.path.isdir(article.get_posts_folder()):
        return template \
            .replace("<TITLE>", article.title) \
            .replace("<EXCERPT_IMAGE>", article.excerpt_image) \
            .replace("<CONTENT>", article.content) \
            .replace("<TAGS>", article.get_tags()) \
            .replace("<FOOTER>", footer_md(article)) \
            .replace("<CATEGORIES>", categories(article)) \
            .replace("<REF>", article.get_ref())
    return "%s is not a folder" % article.get_posts_folder()


# ========================================================================================
def content_md(article) -> str:
    """The full Jekyll file: frontmatter + content + footer. This is what is saved."""
    return templated(article, article.templates["post"])


# ========================================================================================
def content_md_rich(article) -> str:
    md = templated(article, article.templates["content_only"])
    ret = markdown.markdown(md).replace("<a", "<a style='color:%s' " % title_color(article))
    return ret.replace("<p>", "<p style='text-indent: 50px;'>")


# ========================================================================================
def content_md_separators(article) -> str:
    """Styled HTML for the image-card surface (excerpt image floated right, colored titles)."""
    ret = ""
    if article.excerpt_image:
        ret = '<table cellpadding=6 style="float:right;"><tr><td><img src="' \
            + excerpt_image_local(article) + '" width=240 /></td></tr></table>'

    color = title_color(article)
    ret += content_md_rich(article).replace("<h4>", "<h4 align='center'>") \
        .replace("<blockquote>\n<p style='text-indent: 50px;'>",
                 "<blockquote>\n<p style='text-indent: -7px;'><i><b>") \
        .replace("</p>\n</blockquote>", "</b></i></p>\n</blockquote>") \
        .replace("<h1", "<h1 align='center' style='color: %s' " % color) \
        .replace("<h2", "<h2 align='center' style='color: %s' " % color) \
        .replace("<h3", "<h3 align='center' style='color: %s' " % color) \
        .replace("<h4", "<h4 style='color: %s' " % color)
    return ret


# ========================================================================================
def content_md_separators_br(article, add_tags=True) -> str:
    """Line-broken HTML used to derive the social-post text."""
    ret = content_md_rich(article) \
        .replace("<h3>", "<h3 align='center'> ").replace("</h3>", ":</h3>") \
        .replace("<h4>", "<h4 align='center'> ").replace("</h4>", ":</h4>") \
        .replace("<li>", "<li>- ") \
        .replace("<blockquote>\n<p style='text-indent: 50px;'>",
                 "<blockquote>\n<p style='text-indent: -7px;'><i><b>") \
        .replace("</p>\n</blockquote>", "</b></i></p>\n</blockquote>") \
        .replace("</h1>", "</h1 align='center'><br />") \
        .replace("</h2>", "</h2 align='center'><br />") \
        .replace("</p>", "<br /></p>") \
        .replace("</blockquote>", "</blockquote><br />")
    if add_tags:
        ret += hashtags(article.get_tags())
    return ret


# ========================================================================================
def content_short(article) -> str:
    """Title-only rendering + hashtags."""
    ret = templated(article, article.templates["title_only"])
    return markdown.markdown(ret) + "<br />" + hashtags(article.get_tags())


# ========================================================================================
def hashtags(tags) -> str:
    ret = ""
    for t in tags.split(","):
        if t != "Gamsblurb":
            ret += "\n#" + re.sub(r'[^a-zA-Z0-9_ \r\n\t\f\v-]+', '',
                                  unidecode(t).lower()).replace(" ", "")
    return ret


# ========================================================================================
def footer_md(article) -> str:
    footer = ""
    for l in article.links:
        if l.url:
            footer += "- [%s](%s)\n" % (l.text, l.url)
    return footer


# ========================================================================================
def categories(article) -> str:
    cats = [article.get_length_category(), "Gamsblurb"]
    return "[%s]" % ", ".join(map(lambda e: '"%s"' % e, cats))


# ========================================================================================
def plain_text(article) -> str:
    """The exact text a social post would contain (HTML stripped, no hashtags)."""
    soup = BeautifulSoup(content_md_separators_br(article, add_tags=False),
                         features="html.parser")
    return soup.get_text()


# ========================================================================================
def data_url(local_file) -> str:
    """Embed a local file as a data: URL so the webview can render it without
    filesystem origin issues (and html2canvas can capture it untainted).

    Delegates to `localize.file_to_data_url`, which carries the webp/avif MIME
    fallback Windows' `mimetypes` lacks — crucial here, since an `<img>` won't
    render a `data:application/octet-stream` payload."""
    return localize.file_to_data_url(local_file)


# ========================================================================================
def excerpt_image_local(article) -> str:
    """Resolve the excerpt image to something the webview can actually render: a
    local file embedded as a data: URL, or the raw value when it's remote / not
    found on disk.

    Astro stores `image:` as a site-absolute `/assets/posts/<slug>.header.webp`
    that lives under the site's **`public/`** dir — NOT next to the posts folder —
    so resolve against the [[martingamsby-site]] checkout root found by walking up
    from the posts folder (same anchor the localize hook uses). A couple of
    fallbacks keep absolute paths and the legacy blog-relative layout working."""
    src = article.excerpt_image
    if not src or localize.is_remote(src):
        return src

    rel = src.replace("/", os.sep).lstrip(os.sep)
    posts = article.get_posts_folder()
    candidates = []
    if os.path.isabs(src):
        candidates.append(src)
    root = localize.find_repo_root(posts)
    if root:
        candidates.append(os.path.join(root, "public", rel))     # Astro: under public/
    candidates.append(os.path.join(str(Path(posts).parent), rel))  # legacy blog-relative

    for cand in candidates:
        if os.path.isfile(cand):
            return data_url(cand)
    return src
