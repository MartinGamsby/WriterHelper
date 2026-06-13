# Pure-Python ArticleModel: one article in one language (hl). No Qt.
# Every mutation calls updated(), which re-saves the Jekyll .md file.
import configparser
import os
import re

import yaml
from unidecode import unidecode

import filemanager
import rendering

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
        self.excerpt_image = ""
        self.tags = DEFAULT_TAGS
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
        """Persist the article every time anything changes (same contract as the
        old Qt `updated` signal's on_updated slot)."""
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
        return rendering.content_md(self)

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
        self.links = []
        if copy_current:
            print("copy article", self.hl)
            # First, because we want the proper url
            self.set_link(self.get_based_on_text(),
                          self.get_website_url() + self.get_slug(), emit_update=False)
            self.title += " V2"
        else:
            print("new article", self.hl)
            self.title = ""
            self.content = ""
            self.tags = DEFAULT_TAGS
            self.excerpt_image = ""
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
        parts = file_contents.split("---")
        nb_parts = len(parts)
        if nb_parts < 3:
            print("Couldn't parse the md file", nb_parts)
            return False

        self.delete_last = False
        self.date = old_date
        header = yaml.full_load(parts[1].replace("[,Gamsblurb]", "[Gamsblurb]"))
        content = parts[2].strip()

        self.title = header["title"]
        self.content = content.replace("### **%s**" % self.title, "").strip()
        self.excerpt_image = header["excerpt_image"] \
            if ("excerpt_image" in header and header["excerpt_image"]) else ""
        self.determine_length_category()
        self.tags = ",".join(header["tags"]) if "tags" in header else DEFAULT_TAGS

        self.links = []
        if nb_parts == 4:
            # Extract []() style links from the footer
            markup_regex = r'\[([^\[]+)]\(\s*(http[s]?://.+)\s*\)'
            for name, url in re.findall(markup_regex, parts[3]):
                self.set_link(name, url)
                print(url, name)

        if change_ref:
            reference = header.get("ref", "")
            potential_ref_file = self.date + "-" \
                + reference.replace(self.ref.get_website_url(), "") + ".md"
            potential_ref_file_full = os.path.join(self.ref.get_posts_folder(),
                                                   potential_ref_file)
            if os.path.isfile(potential_ref_file_full):
                print("REF:", potential_ref_file_full)
                with open(potential_ref_file_full, mode="r", encoding="utf-8") as f:
                    self.ref.change_article(f.read(),
                                            os.path.basename(potential_ref_file_full)[:10],
                                            change_ref=False)
            else:
                self.ref.new_article()

        self.updated()
        self.delete_last = True
        return True
