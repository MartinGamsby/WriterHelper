from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal, Slot, Property
from PySide6.QtWidgets import QFileDialog

from unidecode import unidecode
import re
import configparser
import os
import re
import yaml
import markdown
from deep_translator import GoogleTranslator

import filemanager

DEFAULT_TAGS = "Gamsblurb"

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
    excerpt_image: str = ""
    #tags = []
    tags = DEFAULT_TAGS#[]
    mini: bool = False
    medium: bool = False
    ref = None
    delete_last = True
    date: str = filemanager.ContentFile().get_date_str()    
    links = None
    green: bool = True
    black: bool = True
    
    updated = Signal()
    
    # ====================================================================================    
    def __init__(self, hl):
        super().__init__()
        self.links = []
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
        #TODO: get_date_str(), OR override (add a textEdit..)
        ##
        self.content_file.create_file(self.get_posts_folder(), self.get_slug(), 
            content=self.content_md(), delete_last=self.delete_last, date_override=self.date)
        
    # ====================================================================================    
    def load_templates(self):        
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates', 'post.md'), mode="r", encoding="utf-8") as f:
            self.template_post_md = f.read()
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates', 'post_content.md'), mode="r", encoding="utf-8") as f:
            self.template_post_content_md = f.read()
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates', 'post_content_only.md'), mode="r", encoding="utf-8") as f:
            self.template_post_content_only_md = f.read()
        
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
    @Slot(None, result=str)
    def get_date(self):
        return self.date        
    @Slot(str, result=bool)
    def set_date(self, date):
        if self.date != date:
            self.date = date
            self.updated.emit()
    p_date = Property(str, get_date, set_date, notify=updated)
    
    # ====================================================================================
    def get_slug(self):
        simple = unidecode(self.title).replace(".","-").replace(" ","-").replace("--","-").replace("--","-").replace("--","-").replace("--","-").lower()
        import re
        return re.sub(r'[^a-zA-Z0-9_ \r\n\t\f\v-]+', '', simple).replace("--","-").rstrip("-")#\W+ is doesn't take spaces and such
        # title\n < éé `kožušček北亰 François
    p_slug = Property(str, get_slug, notify=updated)
           
           
    # ====================================================================================    
    @Slot(str, result=bool)
    def set_content(self, text):
        last_mini = self.mini
        last_medium = self.medium
        self.determine_length_category()        
            
        if self.content != text or self.mini != last_mini or self.medium != last_medium:
            self.content = text
            self.updated.emit()
    @Slot(None, result=str)
    def get_content(self):
        return self.content
    p_content = Property(str, get_content, set_content, notify=updated)
    
    # ====================================================================================   
    def templated(self, template) -> str:
        if os.path.isdir(self.config["Paths"]["Posts"]):
            content = template
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
            
    # ====================================================================================   
    def content_md(self) -> str:
        return self.templated(self.template_post_md)
    p_content_md = Property(str, content_md, notify=updated)
    
    # ====================================================================================   
    def content_md_rich(self) -> str:
        #md = self.templated(self.template_post_content_md)
        md = self.templated(self.template_post_content_only_md)
        #print(markdown.markdown(md))
        # TODO: Better than that ... if I "grabToImage", ... will it include things I put in it? (It can be a component)
        #return '<div align="right" valign="top">test</div>' + markdown.markdown(md)
        
        ret = markdown.markdown(md).replace("<a","<a style='color:%s' " % self.get_title_color())#.replace("</a>","</span")
        #return "<div style='text-indent: 12px;' >" + ret + "<div>"
        return ret.replace("<p>","<p style='text-indent: 50px;'>")
    p_content_md_rich = Property(str, content_md_rich, notify=updated)
                 
    # ====================================================================================   
    def content_md_separators(self) -> str:        
        #ret = self.content_md_rich().replace("<h4>","<h4 align='center'>╞═══╕").replace("</h4>","╘═══╡</h4>") \
        #ret = '<img src="' + self.excerpt_image + '" style="float:right; width: 240px; padding-left: 12px;" width=240 />' + self.content_md_rich().replace("<h4>","<h4 align='center'>╞═══╕").replace("</h4>","╘═══╡</h4>") \
        
        ret = ""
        if self.excerpt_image:
            ret = '<table cellpadding=6 style="float:right;"><tr><td><img src="' + self.excerpt_image + '" width=240 /></td></tr></table>'
        
        ret += self.content_md_rich().replace("<h4>","<h4 align='center'>") \
            .replace("<blockquote>\n<p>","<blockquote>\n<p>&quot;") \
            .replace("</p>\n</blockquote>","&quot;</p>\n</blockquote>") \
            .replace("<h1","<h1 align='center' style='color: %s' " % self.get_title_color()) \
            .replace("<h2","<h2 align='center' style='color: %s' " % self.get_title_color()) \
            .replace("<h3","<h3 align='center' style='color: %s' " % self.get_title_color()) \
            .replace("<h4","<h4 style='color: %s' " % self.get_title_color()) #ade6b9, 099d02, ade6b9
        #print(ret)#("#ade6b9" if self.green else "black")) \
        return ret
    p_content_md_separators = Property(str, content_md_separators, notify=updated)
        
    # ====================================================================================   
    def content_md_separators_br(self) -> str:
        ret = self.content_md_rich() \
            .replace("<h3>","<h3 align='center'>╞══╕").replace("</h3>","╘══╡</h3>") \
            .replace("<h4>","<h4 align='center'>╞══╕").replace("</h4>","╘══╡</h4>") \
            .replace("<li>","<li>- ") \
            .replace("<blockquote>\n<p>","<blockquote>\n<p>&quot;") \
            .replace("</p>\n</blockquote>","&quot;</p>\n</blockquote>") \
            .replace("</h1>","</h1 align='center'><br />") \
            .replace("</h2>","</h2 align='center'><br />") \
            .replace("</p>","<br /></p>") \
            .replace("</blockquote>","</blockquote><br />")
        #print(ret)
        return ret
    p_content_md_separators_br = Property(str, content_md_separators_br, notify=updated)
            
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
    
    # ====================================================================================
    @Slot(bool, result=bool)
    def set_green(self, checked):
        if self.green != checked:
            self.green = checked
            self.updated.emit()
    @Slot(None, result=str)
    def get_green(self):
        return self.green
    p_green = Property(bool, get_green, set_green, notify=updated)
    
    # ====================================================================================
    @Slot(bool, result=bool)
    def set_black(self, checked):
        if self.black != checked:
            self.black = checked
            self.updated.emit()
    @Slot(None, result=str)
    def get_black(self):
        return self.black
    p_black = Property(bool, get_black, set_black, notify=updated)
    
    # ====================================================================================
    def get_title_color(self):
        if self.green:
            return "#ade6b9"
        if self.black:
            return "white"
        return "black"
             
             
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
        
    def get_link(self, name):
        for l in self.links:
            if l.text == name:
                return l.url
        return ""        
    @Slot(None, result=str)
    def get_link_medium(self):
        return self.get_link("Medium")
    @Slot(None, result=str)
    def get_link_x(self):
        return self.get_link("X/Twitter")
    @Slot(None, result=str)
    def get_link_Typeshare(self):
        return self.get_link("Typeshare")
    @Slot(None, result=str)
    def get_link_LinkedIn(self):
        return self.get_link("LinkedIn")
    @Slot(None, result=str)
    def get_link_Facebook(self):
        return self.get_link("Facebook")
    @Slot(None, result=str)
    def get_link_Source(self):
        return self.get_link("Source")
    @Slot(None, result=str)
    def get_link_Bluesky(self):
        return self.get_link("Bluesky")

    p_link_medium = Property(str, get_link_medium, notify=updated)
    p_link_x = Property(str, get_link_x, notify=updated)
    p_link_typeshare = Property(str, get_link_Typeshare, notify=updated)
    p_link_linkedin = Property(str, get_link_LinkedIn, notify=updated)
    p_link_facebook = Property(str, get_link_Facebook, notify=updated)
    p_link_source = Property(str, get_link_Source, notify=updated)
    p_link_bluesky = Property(str, get_link_Bluesky, notify=updated)
    
            
    
    # ====================================================================================    
    @Slot(None, result=bool)
    def get_mini(self):
        return self.mini
    @Slot(bool, result=bool)
    def set_mini(self, mini):
        self.mini = mini
        self.updated.emit()
    p_mini = Property(bool, get_mini, set_mini, notify=updated)
        
    # ====================================================================================   
    @Slot(None, result=bool)
    def get_medium(self):
        return self.medium
    @Slot(bool, result=bool)
    def set_medium(self, medium):
        self.medium = medium
        self.updated.emit()
    p_medium = Property(bool, get_medium, set_medium, notify=updated)
        
    # ====================================================================================    
    def footer_md(self) -> str:
        footer = ""
        for l in self.links:
            if l.url:
                footer += "- [%s](%s)\n" % (l.text, l.url)
        return footer
        
        
    # ====================================================================================    
    def determine_length_category(self):
        self.mini = False
        self.medium = False
        if len(self.content)<280:
            self.mini = True
        elif len(self.content)>2000:
            self.medium = True
        
    # ====================================================================================    
    def get_length_category(self):
        # TODO: Use tr() instead...
        if self.hl == "en":
            if self.medium:
                return "Length: Medium"
            elif self.mini:
                return "Length: Mini"
            else:
                return "Length: Short"
        else:
            if self.medium:
                return "Longueur: Moyen"
            elif self.mini:
                return "Longueur: Mini"
            else:
                return "Longueur: Court"
        
    
    # ====================================================================================    
    def categories(self):
        categories = ["Gamsblurb"]
        categories.insert(0, self.get_length_category())
            
        # double quotes instead of single:
        return "[%s]" % ", ".join(map(lambda e: '"%s"' % e, categories))
        #return str(categories)    
    
    # ====================================================================================     
    @Slot(None, result=bool)
    def new_article(self):
        self.delete_last = False
        
        print("new article", self.hl)
        self.title = ""
        self.date = filemanager.ContentFile().get_date_str()
        self.content = ""
        self.excerpt_image = ""
        self.tags = DEFAULT_TAGS
        self.mini = False
        self.medium = False
        self.links = []
        self.updated.emit()        
        
        self.delete_last = True
        
    # ====================================================================================     
    @Slot(None, result=bool)
    def open_article(self):
        print("open article", self.hl)
        (file_name, _) = QFileDialog.getOpenFileName(None, "Open Article",
            self.get_posts_folder(),
            "Markdown (*.md)")
        if file_name:
            with open(file_name, mode="r", encoding="utf-8") as f:
                file_contents = f.read()
            self.change_article(file_contents, os.path.basename(file_name)[:10])
       
    # ====================================================================================     
    @Slot(None, result=bool)
    def open_next_article(self):
        print("open next article", self.hl)
        last_filename = self.content_file.get_date_slug(self.get_slug(), self.date) + ".md"
        print(last_filename)
        
        found_last_filename = False
        next_filename = ""
        if os.path.isfile(os.path.join(self.get_posts_folder(), last_filename)):
            if last_filename:
                #os.path.join(self.get_posts_folder(), last_filename )#, 
                for f in os.listdir(self.get_posts_folder()):
                    if found_last_filename:
                        next_filename = f
                        break
                    if f == last_filename:
                        found_last_filename = True
        else:
            print("Current file not found")
            
        if next_filename:
            print("Next", next_filename)            
            with open(os.path.join(self.get_posts_folder(), next_filename), mode="r", encoding="utf-8") as f:
                file_contents = f.read()
            self.change_article(file_contents, os.path.basename(next_filename)[:10])
    
    # ====================================================================================     
    @Slot(None, result=bool)
    def post_article(self):
        print("todo")
        pass        
    
    def change_article(self, file_contents, old_date, change_ref=True):
        parts = file_contents.split("---")
        nb_parts = len(parts)
        if nb_parts >= 3:
            self.delete_last = False
            
            self.date = old_date
            
            header = parts[1]
            content = parts[2].strip()
            
            header = yaml.full_load(header.replace("[,Gamsblurb]","[Gamsblurb]"))
            cats = header["categories"]
            
            
            self.title = header["title"]
            self.content = content.replace("### **%s**"%self.title,"").strip()
            self.excerpt_image = header["excerpt_image"] if header["excerpt_image"] else ""
            self.determine_length_category()
            self.tags = ",".join(header["tags"])#[:-1])
            self.links = []
            
            if nb_parts == 4:
                footer = parts[3]

                # https://stackoverflow.com/questions/67940820/how-to-extract-markdown-links-with-a-regex
                # Extract []() style links
                link_name = "[^\[]+"
                link_url = "http[s]?://.+"
                markup_regex = f'\[({link_name})]\(\s*({link_url})\s*\)'

                for match in re.findall(markup_regex, footer):
                    name = match[0]
                    url = match[1]
                    self.set_link(name, url)
                    print(url, name)
        
            if change_ref:
                potential_ref_file = self.date + "-" + header["ref"].replace(self.ref.get_website_url(),"") + ".md"
                potential_ref_file_full = os.path.join( self.ref.get_posts_folder(), potential_ref_file )
                if os.path.isfile(potential_ref_file_full):
                    print( "REF:", potential_ref_file_full )
                    with open(potential_ref_file_full, mode="r", encoding="utf-8") as f:
                        file_contents = f.read()
                        self.ref.change_article(file_contents, os.path.basename(potential_ref_file_full)[:10], change_ref=False)
                
            self.updated.emit()
            self.delete_last = True
            return True
        print("Couldn't parse the md file", nb_parts)
        
        
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
                    
        if dst.content:
            print("SOURCE ALREADY HAS CONTENT!!")
            return
        
        
        if src.title:
            dst.set_title(GoogleTranslator(source=hl, target=dst_hl).translate(src.title))
            
        if src.content:
            dst.set_content(GoogleTranslator(source=hl, target=dst_hl).translate(src.content))
            
        if src.tags:
            dst.set_tags(GoogleTranslator(source=hl, target=dst_hl).translate(src.tags))
            
        if src.get_excerpt_img():
            dst.set_excerpt_img(src.get_excerpt_img())
            
        if src.get_date():
            dst.set_date(src.get_date())
            
        return True
