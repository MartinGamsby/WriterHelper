from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal, Slot, Property

from unidecode import unidecode
import configparser
import os
import re

@dataclass
class ArticleModel(QObject):    
    title: str = ""
    content: str = ""
    posts_folder: str = ""
    
    #updated = Signal(str, arguments=['time'])
    updated = Signal()
    
    def __init__(self):
        super().__init__()
        self.config = configparser.ConfigParser()
        self.config['Paths'] = {'Posts': '.'}
        print("Default", self.config["Paths"]["Posts"])
        self.load_config()
        print("Loaded", self.config["Paths"]["Posts"])
        
    def write_config(self):
        self.config["Paths"]["Posts"] = self.posts_folder
        with open('settings.ini', 'w') as configfile:
          self.config.write(configfile)
          
    def load_config(self):
        self.config.read('settings.ini')
        self.posts_folder = self.config["Paths"]["Posts"]
        
    @Slot(None, result=str)
    def get_posts_folder(self):
        return self.posts_folder

    @Slot(str, result=bool)
    def set_title(self, text):
        # TODO: It's only taking from the UI, it should read from the model at the beginning in the UI, so we can save? (At some point... We don't need MVC for now...)
        if self.title != text:
            self.title = text
            self.updated.emit()
            
    @Slot(str, result=bool)
    def set_content(self, text):
        if self.content != text:
            self.content = text
            self.updated.emit()
            
    @Slot(str, result=bool)
    def set_posts_path(self, text):
        if self.posts_folder != text:
            self.posts_folder = text
            self.write_config()
            self.updated.emit()
            
            
    @Slot(int, result=bool)
    def set_int_select(self, idx):
        print("set_int_select", idx)
    
    @Slot(bool, result=bool)
    def set_bool(self, enabled):
        print("set_bool", enabled)
        
        
    def content_md(self) -> str:
        if os.path.isdir(self.posts_folder):
            return "# %s\n\n%s" % (self.title, self.content)
        else:
            return "%s is not a folder" % self.posts_folder
    def filename_escaped(self):
        simple = unidecode(self.title).replace(" ","-").replace("--","-").lower()
        import re
        return re.sub(r'[^a-zA-Z0-9_ \r\n\t\f\v-]+', '', simple)#\W+ is doesn't take spaces and such
        # title\n < éé `kožušček北亰 François
        
    # We probably need notifications per property ... but python is weird!
    slug = Property(str, filename_escaped, notify=updated)
    