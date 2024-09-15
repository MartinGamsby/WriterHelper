from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal, Slot, Property

from unidecode import unidecode
import configparser
import os
import re
from deep_translator import GoogleTranslator

import filemanager

# ====================================================================================    
@dataclass
class Link(QObject):    
    url: str = ""
    text: str = ""
    
# ====================================================================================    
@dataclass
class ArticleModel(QObject):
    hl: str = ""
    title: str = ""
    content: str = ""
    excerpt_image: str = "/assets/images/default-image.jpeg"
    #tags = []
    tags = ""#[]
    mini: bool = False
    ref = None
    
    links = []
    
    updated = Signal()
    
    # ====================================================================================    
    def __init__(self, hl):
        super().__init__()
        self.content_file = filemanager.ContentFile()
        
        self.updated.connect(self.on_updated)
        
        self.hl = hl
        self.config = configparser.ConfigParser()
        self.config['Paths'] = {'Posts': '.'}
        self.config['URLs'] = {'Website': 'http://'}
        self.load_config()
        print("Loaded", self.hl, self.config["Paths"]["Posts"])
        print("Loaded", self.hl, self.config["URLs"]["Website"])
        
        self.load_templates()
        #self.translator = Translator()
    
    # ====================================================================================    
    def set_ref(self, ref):
        self.ref = ref
    def get_ref(self):
        if self.ref:
            return self.ref.get_website_url() + self.ref.get_slug()
        return ""
        
    # ====================================================================================    
    def on_updated(self):
        self.content_file.create_file(self.get_posts_folder(), self.get_slug(), content=self.content_md())
        
    # ====================================================================================    
    def load_templates(self):        
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates', 'post.md'), mode="r", encoding="utf-8") as f:
            self.template_post_md = f.read()
        
    def config_filename(self):
        return 'settings_%s.ini' % self.hl
        
    def write_config(self):
        with open(self.config_filename(), 'w') as configfile:
          self.config.write(configfile)
          
    def load_config(self):
        self.config.read(self.config_filename())
        
    # ====================================================================================    
    @Slot(None, result=str)
    def get_posts_folder(self):
        return self.config["Paths"]["Posts"]
    @Slot(str, result=bool)
    def set_posts_folder(self, text):
        if self.config["Paths"]["Posts"] != text:
            self.config["Paths"]["Posts"] = text
            self.write_config()
            self.updated.emit()
    p_posts_folder = Property(str, get_posts_folder, set_posts_folder, notify=updated)
    
    # ====================================================================================    
    @Slot(None, result=str)
    def get_website_url(self):
        return self.config["URLs"]["Website"]
    @Slot(str, result=bool)
    def set_website_url(self, text):
        if self.config["URLs"]["Website"] != text:
            self.config["URLs"]["Website"] = text
            self.write_config()
            self.updated.emit()
    p_website_url = Property(str, get_website_url, set_website_url, notify=updated)
            
    # ====================================================================================    
    @Slot(None, result=str)
    def get_title(self):
        return self.title        
    @Slot(str, result=bool)
    def set_title(self, text):
        # TODO: It's only taking from the UI, it should read from the model at the beginning in the UI, so we can save? (At some point... We don't need MVC for now...)
        if self.title != text:
            self.title = text
            self.updated.emit()
    p_title = Property(str, get_title, set_title, notify=updated)
    
    # ====================================================================================
    def get_slug(self):
        simple = unidecode(self.title).replace(" ","-").replace("--","-").lower()
        import re
        return re.sub(r'[^a-zA-Z0-9_ \r\n\t\f\v-]+', '', simple)#\W+ is doesn't take spaces and such
        # title\n < éé `kožušček北亰 François
    p_slug = Property(str, get_slug, notify=updated)
           
           
    # ====================================================================================    
    @Slot(str, result=bool)
    def set_content(self, text):
        if self.content != text:
            self.content = text
            self.updated.emit()            
    @Slot(None, result=str)
    def get_content(self):
        return self.content
    p_content = Property(str, get_content, set_content, notify=updated)
    
    # ====================================================================================   
    def content_md(self) -> str:
        if os.path.isdir(self.config["Paths"]["Posts"]):
            content = self.template_post_md
            return content \
                .replace("<TITLE>", self.title) \
                .replace("<EXCERPT_IMAGE>", self.excerpt_image) \
                .replace("<CONTENT>", self.content) \
                .replace("<TAGS>", self.get_tags()) \
                .replace("<FOOTER>", self.footer_md()) \
                .replace("<CATEGORIES>", self.categories()) \
                .replace("<REF>", self.get_ref())
        else:
            return "%s is not a folder" % self.config["Paths"]["Posts"]
    p_content_md = Property(str, content_md, notify=updated)
             
            
    # ====================================================================================    
    @Slot(None, result=str)
    def get_tags(self):
        return self.tags#(",".join(self.tags))
    @Slot(str, result=bool)
    def set_tags(self, text):
        if self.tags != text:
            self.tags = text
            self.updated.emit()
    p_tags = Property(str, get_tags, set_tags, notify=updated)
        
        
    # ====================================================================================
    @Slot(str, result=bool)
    def set_excerpt_img(self, text):
        if self.excerpt_image != text:
            self.excerpt_image = text
            self.updated.emit()
    @Slot(None, result=str)
    def get_excerpt_img(self):
        return self.excerpt_image
    p_excerpt_img = Property(str, get_excerpt_img, set_excerpt_img, notify=updated)
                        
    #TODO: set_link is weird since bilingual? mixed them? See footer_md?
    # ====================================================================================    
    @Slot(str, str, result=bool)
    def set_link(self, text, url):
        for l in self.links:
            if l.text == text:
                l.url = url
                self.updated.emit()
                return True
        self.links.append(Link(url=url, text=text))
        self.updated.emit()
        return True
            
    
    # ====================================================================================    
    @Slot(bool, result=bool)
    def set_mini(self, mini):
        self.mini = mini
        self.updated.emit()
        
        
    # ====================================================================================    
    def footer_md(self) -> str:
        footer = ""
        for l in self.links:
            if l.url:
                footer += "- [%s](%s)\n" % (l.text, l.url)
        return footer
        
        
    # ====================================================================================    
    def categories(self):
        categories = ["Langue: Français","Langue: Anglais","Gamsblurb"]
        if self.mini:
            categories.insert(0,"Longueur: Mini")
        else:
            categories.insert(0,"Longueur: Court")
            
        # double quotes instead of single:
        return "[%s]" % ", ".join(map(lambda e: '"%s"' % e, categories))
        #return str(categories)
        
    #@Slot(None, result=str)
    #def excerpt_img_local(self):
    #    # TODO: Add another path, next to "posts", but for "images", and paste it there. Use local here.
    #    return "C:\\Users\\Martin\\Documents\\GitHub\\martingamsby.github.io" + self.excerpt_image.replace("/","\\")
    #excerpt_img_local = Property(str, excerpt_img_local, notify=updated)
        
    
        
    # ====================================================================================
    # We probably need notifications per property ... (all p_..)
    
    
    
# ========================================================================================
@dataclass
class ArticlesModel(QObject):
    french: ArticleModel = ArticleModel(hl="fr")
    english: ArticleModel = ArticleModel(hl="en")
    
    # ====================================================================================    
    def __init__(self):
        super().__init__()
        self.french.set_ref(self.english)
        self.english.set_ref(self.french)
        
    # ====================================================================================
    @Slot(None, result=ArticleModel)
    def fr(self):
        return self.french
    @Slot(None, result=ArticleModel)
    def en(self):
        return self.english

    # ====================================================================================    
    @Slot(str, result=bool)
    def translate(self, hl):
        print("translate", hl)
        
        if hl == "en":        
            src = self.en()
            dst = self.fr()
            dst_hl = "fr"
        else:
            src = self.fr()
            dst = self.en()
            dst_hl = "en"
                    
        if src.title:
            dst.set_title(GoogleTranslator(source=hl, target=dst_hl).translate(src.title))
            
        if src.content:
            dst.set_content(GoogleTranslator(source=hl, target=dst_hl).translate(src.content))
            
        if src.tags:
            dst.set_tags(GoogleTranslator(source=hl, target=dst_hl).translate(src.tags))
            
        if src.get_excerpt_img():
            dst.set_excerpt_img(src.get_excerpt_img())
        return True
