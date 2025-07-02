import os
from atproto import Client
from post import Post

# ====================================================================================    
class PostBsky(Post):

    # ====================================================================================    
    def __init__(self, hl):
        Post.__init__(self, hl, access={'Handle': '<TODO>', 'AppPassword': '<TODO>'})
    
    # ====================================================================================    
    def post(self, msg, image_local_url, alt_text):
        client = Client()
        
        client.login(self.get_handle(), self.get_app_password())
        
        if image_local_url and os.path.isfile(image_local_url):
            with open(image_local_url, 'rb') as f:
                img_data = f.read()
                post = client.send_image(text=msg, image=img_data, image_alt=alt_text, langs=[self.hl])
        else:
            post = client.send_post(msg, langs=[self.hl])
            
        # More than text here: https://docs.bsky.app/docs/tutorials/creating-a-post
        # For example embeds for youtube?
        
        uri = post.uri
        handle = self.get_handle()
        
        # e.g.
        # at://did:plc:56ydoq55hhqiyon2kbvt7gd6/app.bsky.feed.post/3ls52v3vmiy2p
        # https://bsky.app/profile/martin-gamsby.bsky.social/post/
        #uri = "at://did:plc:56ydoq55hhqiyon2kbvt7gd6/app.bsky.feed.post/3ls52v3vmiy2p"
        #handle = "martin-gamsby.bsky.social"        
        id = uri[uri.rfind("/")+1:]
        url = f"https://bsky.app/profile/{handle}/post/{id}"
        return url
            
    # ====================================================================================    
    def config_filename(self):
        return 'settings_bsky_%s.ini' % self.hl

# ====================================================================================        
if __name__ == '__main__':
    print("Commented to prevent accidental post")
    #bsky_en = PostBsky("en")
    #res = bsky_en.post(msg='Hello world! I posted this via the Python SDK.',
    #                image_local_url="richTextArea_en1.png")
    #print("Result:", res)
    