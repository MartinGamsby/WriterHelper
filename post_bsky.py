import os
from atproto import Client
import configparser

# ====================================================================================    
class PostBsky():

    # ====================================================================================    
    def __init__(self, hl):        
        self.hl = hl
        self.config = configparser.ConfigParser()
        self.config['Access'] = {'Handle': '<TODO>', 'AppPassword': '<TODO>'}
        self.load_config()
        #print("Loaded", self.hl, self.get_app_password() )
        print(f"Loaded Page ID: '{self.hl}', @{self.get_handle()}" )
    
    def get_handle(self):
        return self.config["Access"]["Handle"]
        
    def get_app_password(self):
        return self.config["Access"]["AppPassword"]
        
    # ====================================================================================    
    def post(self, msg, image_local_url):
        client = Client()
        
        client.login(self.get_handle(), self.get_app_password())
        
        if image_local_url and os.path.isfile(image_local_url):
            with open(image_local_url, 'rb') as f:
                img_data = f.read()
                post = client.send_image(text=msg, image=img_data, image_alt=msg, langs=[self.hl])
        else:
            post = client.send_post(msg, langs=[self.hl])
            
        # More than text here: https://docs.bsky.app/docs/tutorials/creating-a-post
        # For example embeds for youtube?
        return post
            
    # ====================================================================================    
    def config_filename(self):
        return 'settings_bsky_%s.ini' % self.hl
        
    # ====================================================================================    
    def load_config(self):
        if os.path.isfile(self.config_filename()):
            self.config.read(self.config_filename())
        else:
            self.write_default_config()
        
    def write_default_config(self):
        with open(self.config_filename(), 'w') as configfile:
          self.config.write(configfile)
          
# ====================================================================================        
if __name__ == '__main__':
    pass
    #bsky_en = PostBsky("en")
    #res = bsky_en.post(msg='Hello world! I posted this via the Python SDK.',
    #                image_local_url="richTextArea_en1.png")
    #print("Result:", res)
    