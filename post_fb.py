# THIS WAS A TEST AND IT IS NOT WORKING YET
import requests
import configparser

# ====================================================================================    
class PostFB():

    # ====================================================================================    
    def __init__(self, hl):        
        self.hl = hl
        self.config = configparser.ConfigParser()
        self.config['Access'] = {'Token': ''}
        self.config['Access'] = {'PageId': ''}
        self.load_config()
        #print("Loaded", self.hl, self.get_token() )
        print("Loaded Page ID: ", self.hl, self.get_page_id() )
    
    def get_token(self):
        return self.config["Access"]["Token"]
        
    def get_page_id(self):
        return self.config["Access"]["PageId"]
        
    # ====================================================================================    
    def post_to_fb_page(self, msg, image_url):
        if image_url:
            post_url = 'https://graph.facebook.com/v18.0/{}/photos'.format(self.get_page_id())
            payload = {
                'message': msg,
                'access_token': self.get_token(),
                'url': image_url
            }
        else:
            post_url = 'https://graph.facebook.com/v18.0/{}/feed'.format(self.get_page_id())
            payload = {
                'message': msg,
                'access_token': self.get_token()
            }
            
        # Uploading on FB Group
        r = requests.post(post_url, data=payload)
        data = r.json()
        print(data)
        if 'id' in data:
            return True
        else:
            return False
            
    # ====================================================================================    
    def config_filename(self):
        return 'fb_settings_%s.ini' % self.hl
        
    # ====================================================================================    
    def load_config(self):
        self.config.read(self.config_filename())
        
# ====================================================================================        
if __name__ == '__main__':
    fb_fr = PostFB("fr")
    res =fb_fr.post_to_fb_page(msg='Test',
                    image_url=None)#'https://www.allrecipes.com/thmb/d7iH4d7LSY0c6aI98G-3AwLZTWw=/800x533/filters:no_upscale():max_bytes(150000):strip_icc():focal(399x0:401x2):format(webp)/263037-instant-pot-beef-stew-mfs-beauty-1x1-BP-2467-80aedb6795b84febbedc172f6d921c14.jpg')
    print("Result:", res)