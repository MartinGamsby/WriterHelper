import sys

import os
import subprocess


# ========================================================================================
from PySide6.QtCore import QTimer, QObject, Signal, Slot

import model
import filemanager


# ========================================================================================
class Backend(QObject):

    # ====================================================================================
    def __init__(self):
    
        french=model.ArticleModel(hl="fr")
        english=model.ArticleModel(hl="en")
        french.set_ref(english)
        english.set_ref(french)
        
        self.articles = model.ArticlesModel(french, english)
        
        french.open_last_article()
        
        super().__init__()

    # ====================================================================================
    @Slot(str, result=bool)
    def run(self, arg):
        args = arg.split()

        args = [os.path.expandvars(i) for i in args]
        print(args)
        subprocess.run(args)
        return True

    # ====================================================================================
    @Slot()
    def quit(self):
        print("quitting")

    # ====================================================================================
    @Slot(str, result=bool)
    def translate(self, hl):
        return self.articles.translate(hl)
                
    # ====================================================================================
    @Slot(None, result=model.ArticlesModel)
    def articles(self):
        return self.articles
        
    # ====================================================================================
    @Slot(str, result=model.ArticleModel)
    def article(self, hl):
        if hl == "en":
            return self.articles.en()
        return self.articles.fr()
        
    # ====================================================================================
    @Slot(str, result=str)
    def get_used_tags(self, hl): # TODO: Better than that...
        tags = {}
        
        folder = self.article(hl).get_posts_folder()
        date_str = filemanager.ContentFile.get_date_str()
                
        if os.path.isdir(folder):
            for f in os.listdir(folder):
                full_f = os.path.join(folder,f)
                if f.endswith("md") and not f.startswith(date_str):# For the current file
                    #print(full_f)
                    with open(full_f, mode="r", encoding="utf-8") as f:
                        #f.read()
                        #print(full_f, f.read())
                                        
                        # Strips the newline character
                        for line in f.readlines():
                            if line.startswith("tags"):
                                start = line.index("[")+1
                                end = line.index("]")
                                l = line[start:end]                                
                                t = l.split(",")
                                for tag in t:
                                    stripped = tag.strip()
                                    if not stripped in tags:
                                        tags[stripped] = 1
                                    else:
                                        tags[stripped] += 1
        #print(tags)
        sorted_tags = sorted(tags.items(), key=lambda x:x[1], reverse=True)
        
        tags_str = ""
        for t in sorted_tags:
            tags_str += t[0] + ", "
        return tags_str
        #return ",".join(tags)
        
