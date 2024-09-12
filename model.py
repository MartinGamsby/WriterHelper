from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal, Slot, Property

from unidecode import unidecode
import configparser
import os
import re
#from googletrans import Translator
from deep_translator import GoogleTranslator

@dataclass
class Link(QObject):    
    url: str = ""
    text: str = ""
    
@dataclass
class ArticleModel(QObject):    
    title: str = ""
    content: str = ""
    excerpt_image: str = "/assets/images/default-image.jpeg"
    #tags = []
    tags = ""#[]
    mini: bool = False
    
    links = []
    
    updated = Signal()
    updated_en = Signal()
    
    def __init__(self):
        super().__init__()
        self.config = configparser.ConfigParser()
        self.config['Paths'] = {'Posts': '.'}
        print("Default", self.config["Paths"]["Posts"])
        self.load_config()
        print("Loaded", self.config["Paths"]["Posts"])
        
        self.load_templates()
        #self.translator = Translator()
        
    def load_templates(self):        
        with open(os.path.join('templates', 'post.md'), mode="r", encoding="utf-8") as f:
            self.template_post_md = f.read()
        
    def write_config(self):
        with open('settings.ini', 'w') as configfile:
          self.config.write(configfile)
          
    def load_config(self):
        self.config.read('settings.ini')
        
    @Slot(None, result=str)
    def get_posts_folder(self):
        return self.config["Paths"]["Posts"]

    @Slot(str, result=bool)
    def set_posts_folder(self, text):
        if self.config["Paths"]["Posts"] != text:
            self.config["Paths"]["Posts"] = text
            self.write_config()
            self.updated.emit()
            
    @Slot(str, result=bool)
    def set_title(self, text):
        # TODO: It's only taking from the UI, it should read from the model at the beginning in the UI, so we can save? (At some point... We don't need MVC for now...)
        if self.title != text:
            self.title = text
            self.updated.emit()
            
    @Slot(str, result=bool)
    def set_tags(self, text):
        if self.tags != text:
            self.tags = text
            self.updated.emit()
            
            
    @Slot(str, result=bool)
    def set_content(self, text):
        if self.content != text:
            self.content = text
            self.updated.emit()
            
            
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
        
    @Slot(str, result=bool)
    def set_link_medium(self, text):
        if self.title != text:
            self.title = text
            self.updated.emit()
            
            
            
    @Slot(int, result=bool)
    def set_int_select(self, idx):
        print("set_int_select", idx)
    
    @Slot(bool, result=bool)
    def set_mini(self, mini):
        self.mini = mini
        self.updated.emit()
        
        
    def footer_md(self) -> str:
        footer = ""
        for l in self.links:
            if l.url:
                footer += "- [%s](%s)\n" % (l.text, l.url)
        return footer
        
    @Slot(None, result=str)
    def get_tags(self):
        return self.tags#(",".join(self.tags))
        
    def categories(self):
        categories = ["Langue: Français","Langue: Anglais","Gamsblurb"]
        if self.mini:
            categories.insert(0,"Longueur: Mini")
        else:
            categories.insert(0,"Longueur: Court")
            
        # double quotes instead of single:
        return "[%s]" % ", ".join(map(lambda e: '"%s"' % e, categories))
        #return str(categories)
        
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
                
                
            #return "# %s\n\n%s" % (self.title, self.content)
        else:
            return "%s is not a folder" % self.config["Paths"]["Posts"]
            
    def filename_escaped(self):
        simple = unidecode(self.title).replace(" ","-").replace("--","-").lower()
        import re
        return re.sub(r'[^a-zA-Z0-9_ \r\n\t\f\v-]+', '', simple)#\W+ is doesn't take spaces and such
        # title\n < éé `kožušček北亰 François
        
    @Slot(str, result=bool)
    def set_excerpt_image(self, text):
        if self.excerpt_image != text:
            self.excerpt_image = text
            self.updated.emit()
    @Slot(None, result=str)
    def get_excerpt_image(self):
        return self.excerpt_image
        
    @Slot(None, result=str)
    def excerpt_img_local(self):
        # TODO: Add another path, next to "posts", but for "images", and paste it there. Use local here.
        return "C:\\Users\\Martin\\Documents\\GitHub\\martingamsby.github.io" + self.excerpt_image.replace("/","\\")
        
    @Slot(None, result=str)
    def get_title_en(self):
        #res = self.translator.translate(self.title, src="fr", dest="en")
        #print(res)
        res = GoogleTranslator(source='fr', target='en').translate(self.title)
        return res
        
    @Slot(None, result=str)
    def get_content_en(self):
        res = GoogleTranslator(source='fr', target='en').translate(self.content)
        return res
        
    # ====================================================================================
    @Slot(None, result=bool)
    def translate(self):
        print("translate")
        self.updated_en.emit()
        return True

        
    # We probably need notifications per property ... but python is weird!
    slug = Property(str, filename_escaped, notify=updated)
    excerpt_img = Property(str, get_excerpt_image, notify=updated)
    excerpt_img_local = Property(str, excerpt_img_local, notify=updated)
    
    title_en = Property(str, get_title_en, notify=updated_en)
    content_en = Property(str, get_content_en, notify=updated_en)
    