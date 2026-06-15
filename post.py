import os
import configparser

# ====================================================================================    
class Post():

    # ====================================================================================    
    def __init__(self, hl, access={'Handle': '<TODO>', 'AppPassword': '<TODO>'}):
        self.hl = hl
        self.config = configparser.ConfigParser()
        self.config['Access'] = access
        self.load_config()
        print(f"Loaded Page ID: '{self.hl}', @{self.get_handle()}" )
    
    def get_handle(self):
        return self.config["Access"]["Handle"]
        
    def get_app_password(self):
        return self.config["Access"]["AppPassword"]
                
    # ====================================================================================
    def post(self, msg, image_local_url, alt_text):
        print("To implement")

    # ====================================================================================
    def post_thread(self, messages, image_local_url, alt_text):
        """Post `messages` as a reply chain, returning a URL per post (first = root).
        `image_local_url` (if any) attaches to the first post only. Platform-specific
        — adapters override; the base has no generic reply mechanism."""
        raise NotImplementedError("This platform does not support threads")

    # ====================================================================================    
    def config_filename(self):
        return 'settings_TODO_%s.ini' % self.hl
        
    # ====================================================================================    
    def load_config(self):
        if os.path.isfile(self.config_filename()):
            self.config.read(self.config_filename())
        else:
            self.write_default_config()
        
    def write_default_config(self):
        with open(self.config_filename(), 'w') as configfile:
          self.config.write(configfile)
       
