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
        
        #print(self.get_all_articles("en"))
        
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
        return "" # It was becoming slow... and was not super helpful. Need to add links to add them in the list.
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
        

    # ====================================================================================
    @Slot(str, result=str)
    def get_all_articles(self, hl): # TODO: Better than that...
        text = ""
        
        folder = self.article(hl).get_posts_folder()
                
        if os.path.isdir(folder):
            files = os.listdir(folder)
            files.reverse()
            for f in files:
                full_f = os.path.join(folder,f)
                if f.endswith("md"):
                    
                    text += "\n"
                    #with open(full_f, mode="r", encoding="utf-8") as f:
                    #    text += f.read()
                    
                    with open(full_f, mode="r", encoding="utf-8") as file:
                        for i, line in enumerate(file.readlines()):
                            if i == 1:                                
                                text += "date: " + f[:10] + "\n"
                                text += "name: " + f[11:-3] + "\n"
                                
                            skip = False
                            for prefix in ["layout: ", "title: ", "categories: ", "excerpt_image: ", "ref: ", "- [Typeshare]", "- [X/Twitter]", "- [Medium]", "- [LinkedIn]", "- [Facebook]", "- [Source]", "- [Bluesky]", "- [YouTube", "- [Based on]"]:
                                if line.startswith(prefix):
                                    skip = True
                                    break
                                    
                            if not skip:
                                text += line + "\n"
                                        
                    text += "\n"
                                        
        
        return text
        