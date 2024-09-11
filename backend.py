import time
import sys

import os
import subprocess
import threading
from datetime import datetime


# ========================================================================================
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QTimer, QObject, Signal, Slot

from time import strftime, localtime
import model


# ========================================================================================
class Backend(QObject):

    initialized = Signal() 
    updated = Signal(str, arguments=['time']) 

    # ====================================================================================
    def __init__(self):
        super().__init__()
        self.model = model.ArticleModel()
        self.model.updated.connect(self.on_model_updated)
        self.is_initialized=False
        self.last_filename = ""
        self.file_lock = threading.Lock()

        # Define timer.
        #self.timer = QTimer()
        #self.timer.setInterval(1000)
        #self.timer.timeout.connect(self.on_model_updated)
        #self.timer.start()

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
    @Slot(None, result=model.ArticleModel)
    def data(self):
        return self.model
        
    # ====================================================================================
    def get_time(self):
        return strftime("%H:%M:%S", localtime())

    def on_model_updated(self):
        if not self.is_initialized:
            self.is_initialized = True
            self.initialized.emit()
            
        data = self.model.content_md()
        self.create_file(self.model.get_posts_folder(), self.model.filename_escaped(), content=data)
        self.updated.emit(data)



    # ====================================================================================
    @staticmethod
    def get_date_str():
        n = datetime.now()
        date_str = n.strftime("%Y-%m-%d")
        return date_str

    # ====================================================================================
    @staticmethod
    def check_post_exists(folder, filename):
        exists = False
        if os.path.isdir(folder):
            for f in os.listdir(folder):
                full_f = os.path.join(folder,f)
                if f.startswith(filename):#TODO: Backend.get_date_str() instead?
                    exists = True
                    #print(f, full_f)
        
        return exists
        
        
    # ====================================================================================
    def create_file(self, folder, filename, content):
        filename = Backend.get_date_str() + "-" + filename + ".md"
        #print( "filename", filename )
        
        with self.file_lock:
            #if Backend.check_post_exists(folder, filename):
            #    print("File for %s already exists" % filename)
            #else:
            new_file = os.path.join(folder, filename)
            with open(new_file, "w") as file:
                file.write(content)
            #print("Wrote '%s'" % new_file)
            
            
            if self.last_filename != filename:
                last_filename = os.path.join(folder, self.last_filename)
                if os.path.isfile(last_filename):
                    if Backend.check_post_exists(folder, self.last_filename):
                        os.remove(last_filename)
                        print("Deleting old name ", self.last_filename)
                self.last_filename = filename
            
    # ====================================================================================
    @Slot(None, result=str)
    def get_used_tags(self):
        tags = {}
        
        folder = self.model.get_posts_folder()
        date_str = self.get_date_str()
                
        if os.path.isdir(folder):
            for f in os.listdir(folder):
                full_f = os.path.join(folder,f)
                if f.endswith("md") and not f.startswith(date_str):
                    print(full_f)
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
                                    if not tag in tags:
                                        tags[tag] = 1
                                    else:
                                        tags[tag] += 1
        #print(tags)
        sorted_tags = sorted(tags.items(), key=lambda x:x[1], reverse=True)
        
        tags_str = ""
        for t in sorted_tags:
            tags_str += t[0] + ","
        return tags_str
        #return ",".join(tags)
        
