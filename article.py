# Pure-Python ArticleModel: one article in one language (hl). No Qt.
# Every mutation calls updated(), which re-saves the .md file in the Astro format.
import configparser
import os
import re

from unidecode import unidecode

import filemanager
import localize
import rendering
import serializers

DEFAULT_TAGS = "Gamsblurb"


# ========================================================================================
class Link:
    def __init__(self, text="", url=""):
        self.text = text
        self.url = url


# ========================================================================================
class ArticleModel:

    # ====================================================================================
    def __init__(self, hl, config_dir="."):
        self.hl = hl
        self.title = ""
        self.content = ""
        self.excerpt_image = ""   # header/OG image — a local path once localized
        self.image_thumb = ""     # small list thumbnail, set by the localize hook
        self.tags = DEFAULT_TAGS
        self.facets = []          # pair-shared: dev|physics|fiction|music|ideas
        self.draft = False        # pair-shared: hides the post from the site build
        self.translation_key = ""  # sticky pairing key; see get_translation_key
        self.mini = False
        self.medium = False
        self.ref = None
        self.delete_last = True
        self.green = True
        self.black = True
        self.links = []
        self.date = filemanager.ContentFile.get_date_str()
        self.content_file = filemanager.ContentFile()
        self.config_dir = config_dir

        self.config = configparser.ConfigParser()
        self.config['Paths'] = {'Posts': '.'}
        self.config['URLs'] = {'Website': 'http://'}
        self.load_config()
        print("Loaded", self.hl, self.config["Paths"]["Posts"])
        print("Loaded", self.hl, self.config["URLs"]["Website"])

        self.templates = rendering.load_templates()

    # ====================================================================================
    def updated(self):
        """Persist the article (Astro format) every time anything changes (same
        contract as the old Qt `updated` signal's on_updated slot)."""
        if not self.get_slug():
            # A title-less article has no filename — don't write a stray `<date>-.md`.
            return
        self.content_file.create_file(self.get_posts_folder(), self.get_slug(),
                                      content=self.content_md(),
                                      delete_last=self.delete_last,
                                      date_override=self.date)

    # ====================================================================================
    def config_filename(self):
        return os.path.join(self.config_dir, 'settings_%s.ini' % self.hl)

    def write_config(self):
        with open(self.config_filename(), 'w') as configfile:
            self.config.write(configfile)

    def load_config(self):
        self.config.read(self.config_filename())

    # ====================================================================================
    def set_ref(self, ref):
        self.ref = ref

    def get_ref(self):
        if self.ref:
            return self.ref.get_website_url() + self.ref.get_slug()
        return ""

    # ====================================================================================
    # Astro pairing + URLs
    def get_translation_key(self):
        """Sticky pairing key, IDENTICAL in both languages' files — this is what the
        Astro site uses to link FR↔EN. Resolution order:

          1. this side already has a key  → return it (frozen: survives title/date
             edits, so the filename/URL can move without breaking published links);
          2. the ref already has a key     → adopt it (keeps the pair in lock-step,
             e.g. after re-translating one side into a fresh `new_article`);
          3. neither does                  → mint `<date>-<EN-slug>` (falling back to
             this language's slug while EN is still untitled) and stamp it onto BOTH
             self AND ref so the two files can NEVER diverge.

        Whichever side first needs a key mints it for the whole pair; the other side
        adopts it on its next save. The minted value is arbitrary — all that matters
        is that both files carry the same `translationKey`. No file is written here
        (pure w.r.t. disk); the shared key lands on disk through the normal save flow.
        Round-tripped from disk on load; cleared by `new_article` for a fresh post."""
        if self.translation_key:
            return self.translation_key
        if self.ref is not None and self.ref.translation_key:
            self.translation_key = self.ref.translation_key
            return self.translation_key

        en = self if self.hl == "en" else self.ref
        base_slug = (en.get_slug() if en else "") or self.get_slug()
        if not base_slug:                 # both sides untitled — nothing to key on yet
            return ""
        date = en.date if (en and en.date) else self.date
        self.translation_key = date + "-" + base_slug
        if self.ref is not None:
            self.ref.translation_key = self.translation_key
        return self.translation_key

    def get_post_url(self):
        """Public Astro URL of this article: `<website>/<date>-<slug>/`."""
        stem = self.content_file.get_date_slug(self.get_slug(), self.date)
        return self.get_website_url() + stem + "/"

    # facets and draft are shared across the FR/EN pair (like `date`): setting one
    # mirrors the value onto the ref and persists both.
    def set_facets(self, facets):
        facets = [str(f) for f in facets if f]
        if self.facets != facets:
            self.facets = facets
            if self.ref is not None and self.ref.facets != facets:
                self.ref.facets = list(facets)
                self.ref.updated()
            self.updated()

    def set_draft(self, draft):
        draft = bool(draft)
        if self.draft != draft:
            self.draft = draft
            if self.ref is not None and self.ref.draft != draft:
                self.ref.draft = draft
                self.ref.updated()
            self.updated()

    # ====================================================================================
    # Simple fields: each setter persists via updated() only on real change.
    def get_posts_folder(self):
        return self.config["Paths"]["Posts"]

    def set_posts_folder(self, text):
        if self.config["Paths"]["Posts"] != text:
            self.config["Paths"]["Posts"] = text
            self.write_config()
            self.updated()

    def get_website_url(self):
        return self.config["URLs"]["Website"]

    def set_website_url(self, text):
        if self.config["URLs"]["Website"] != text:
            self.config["URLs"]["Website"] = text
            self.write_config()
            self.updated()

    def get_title(self):
        return self.title

    def set_title(self, text):
        if self.title != text:
            self.title = text
            self.updated()

    def get_date(self):
        return self.date

    def set_date(self, date):
        if self.date != date:
            self.date = date
            self.updated()

    def get_content(self):
        return self.content

    def set_content(self, text):
        if self.content != text:
            self.content = text
            self.determine_length_category()
            self.updated()

    def get_tags(self):
        return self.tags

    def set_tags(self, text):
        if self.tags != text:
            self.tags = text
            self.updated()

    def get_excerpt_img(self):
        return self.excerpt_image

    def set_excerpt_img(self, text):
        if self.excerpt_image != text:
            self.excerpt_image = text
            self.image_thumb = ""   # old thumbnail no longer matches the new image
            self.updated()
            self._localize_excerpt_image()

    def _localize_excerpt_image(self):
        """If the image is a remote URL, self-host it via the site hook and store
        the returned local image/thumbnail paths (the file is already rewritten;
        we just keep the model in sync so later edits don't re-hot-link).

        A dropped/opened image arrives as a `data:` URL — fine as input, but it
        must NEVER be left persisted: a failed self-host would otherwise commit a
        100KB+ base64 blob into the post. The hook can fail transiently (node/sharp
        cold start, a momentary file lock), so for a `data:` value we retry once
        and, if it still fails, drop the image and re-save rather than persist the
        blob. A plain remote http(s) URL that fails is left in place (it's small
        and still renders)."""
        if not localize.is_remote(self.excerpt_image):
            return
        is_data = self.excerpt_image.startswith("data:")
        md_path = os.path.join(
            self.get_posts_folder(),
            self.content_file.get_date_slug(self.get_slug(), self.date) + ".md")
        image, thumb = localize.localize_file(md_path)
        if not image and is_data:
            image, thumb = localize.localize_file(md_path)   # one retry; the blob is at stake
        if image:
            self.excerpt_image = image
            self.image_thumb = thumb
        elif is_data:
            print("localize: could not self-host dropped image; dropping it so the "
                  "post never carries a base64 blob")
            self.excerpt_image = ""
            self.image_thumb = ""
            self.updated()

    def set_green(self, checked):
        if self.green != checked:
            self.green = checked
            self.updated()

    def set_black(self, checked):
        if self.black != checked:
            self.black = checked
            self.updated()

    # ====================================================================================
    def get_slug(self):
        simple = unidecode(self.title).replace(".", "-").replace(" ", "-") \
            .replace("--", "-").replace("--", "-").replace("--", "-").replace("--", "-").lower()
        return re.sub(r'[^a-zA-Z0-9_ \r\n\t\f\v-]+', '', simple).replace("--", "-").rstrip("-")

    # ====================================================================================
    # Rendering flavors (delegates — see rendering.py)
    def content_md(self):
        """The saved file: Astro markdown (see serializers.serialize)."""
        return serializers.serialize(self)

    def content_md_rich(self):
        return rendering.content_md_rich(self)

    def content_md_separators(self):
        return rendering.content_md_separators(self)

    def content_md_separators_br(self, add_tags=True):
        return rendering.content_md_separators_br(self, add_tags)

    def content_short(self):
        return rendering.content_short(self)

    # ====================================================================================
    # Links
    def set_link(self, text, url, emit_update=True):
        for l in self.links:
            if l.text == text:
                l.url = url
                self.updated()
                return True
        self.links.append(Link(url=url, text=text))
        if emit_update:
            self.updated()
        return True

    def get_link(self, name):
        for l in self.links:
            if l.text == name:
                return l.url
        return ""

    def get_based_on_text(self):
        if self.hl == "fr":
            return "Basé sur"
        return "Based on"

    # ====================================================================================
    def determine_length_category(self):
        self.mini = len(self.content) < 280
        self.medium = len(self.content) > 2000

    def get_length_category(self):
        if self.hl == "en":
            return "Length: Medium" if self.medium else \
                   "Length: Mini" if self.mini else "Length: Short"
        return "Longueur: Moyen" if self.medium else \
               "Longueur: Mini" if self.mini else "Longueur: Court"

    # ====================================================================================
    def new_article(self, copy_current=False):
        self.delete_last = False
        # A new post is not a rename of the previous one: forget the last filename so the
        # first save can't rename-by-delete the article we just left. (A blank new article
        # skips updated() on its empty slug, so last_filename would otherwise still point
        # at the previous real file and the next keystroke would delete it.)
        self.content_file.last_filename = ""
        self.links = []
        self.translation_key = ""     # a fresh post gets a fresh pairing key
        if copy_current:
            print("copy article", self.hl)
            # First, because we want the proper url
            self.set_link(self.get_based_on_text(),
                          self.get_post_url(), emit_update=False)
            self.title += " V2"
        else:
            print("new article", self.hl)
            self.title = ""
            self.content = ""
            self.tags = DEFAULT_TAGS
            self.excerpt_image = ""
            self.image_thumb = ""
            self.facets = []
            self.draft = False
        self.date = filemanager.ContentFile.get_date_str()
        self.mini = False
        self.medium = False
        self.updated()
        self.delete_last = True

    # ====================================================================================
    def new_both_articles(self, copy_current=False):
        self.delete_last = False
        self.ref.new_article(copy_current=copy_current)
        self.new_article(copy_current=copy_current)
        self.delete_last = True

    # ====================================================================================
    def load_file(self, file_name):
        with open(file_name, mode="r", encoding="utf-8") as f:
            file_contents = f.read()
        return self.change_article(file_contents, os.path.basename(file_name)[:10])

    # ====================================================================================
    def open_last_article(self):
        print("open last article", self.hl)
        last_filename = ""
        for f in os.listdir(self.get_posts_folder()):
            if f.endswith(".md") and os.path.isfile(os.path.join(self.get_posts_folder(), f)):
                last_filename = f
        if last_filename:
            print("Last", last_filename)
            self.load_file(os.path.join(self.get_posts_folder(), last_filename))

    # ====================================================================================
    def open_next_article(self):
        self.open_adjacent_article(to_previous=False)

    def open_prev_article(self):
        self.open_adjacent_article(to_previous=True)

    def open_adjacent_article(self, to_previous):
        last_filename = self.content_file.get_date_slug(self.get_slug(), self.date) + ".md"
        found_last_filename = False
        next_filename = ""
        if os.path.isfile(os.path.join(self.get_posts_folder(), last_filename)):
            files = os.listdir(self.get_posts_folder())
            if to_previous:
                files.reverse()
            for f in files:
                if found_last_filename:
                    next_filename = f
                    break
                if f == last_filename:
                    found_last_filename = True
        else:
            print("Current file not found")
        if next_filename:
            print("Next", next_filename)
            self.load_file(os.path.join(self.get_posts_folder(), next_filename))

    # ====================================================================================
    def change_article(self, file_contents, old_date, change_ref=True):
        """Load a saved post into this model. Format (Jekyll vs Astro) is
        auto-detected; see serializers.parse."""
        return serializers.parse(self, file_contents, old_date, change_ref)
