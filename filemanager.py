import os
import threading
from datetime import datetime
from time import strftime, localtime


# ========================================================================================
class ContentFile():

    # ====================================================================================
    def __init__(self):
        self.last_filename = ""
        self.file_lock = threading.Lock()

        super().__init__()

    # ====================================================================================
    def get_time(self):
        return strftime("%H:%M:%S", localtime())

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
                if f.startswith(filename):#TODO: ContentFile.get_date_str() instead?
                    exists = True
                    #print(f, full_f)
        
        return exists
        
    # ====================================================================================
    def get_date_slug(self, slug):
        return ContentFile.get_date_str() + "-" + slug
        
    # ====================================================================================
    def create_file(self, folder, filename, content):
        filename = self.get_date_slug(filename) + ".md"
        
        with self.file_lock:
            #if ContentFile.check_post_exists(folder, filename):
            #    print("File for %s already exists" % filename)
            #else:
            new_file = os.path.join(folder, filename)
            with open(new_file, "w", encoding="utf-8") as file:
                file.write(content)
            
            
            if self.last_filename != filename:
                last_filename = os.path.join(folder, self.last_filename)
                if os.path.isfile(last_filename):
                    if ContentFile.check_post_exists(folder, self.last_filename):
                        os.remove(last_filename)
                        print("Deleting old name ", self.last_filename)
                self.last_filename = filename
            