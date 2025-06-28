import os
import tweepy
from post import Post

# ====================================================================================    
class PostX(Post):

    # ====================================================================================    
    def __init__(self, hl):
        Post.__init__(self, hl, access={'Handle': '<TODO>', 
            'APIKey': '<TODO>', 
            'APISecret': '<TODO>',
            'BearerToken': '<TODO>',
            'AccessToken': '<TODO>',
            'AccessSecret': '<TODO>',
            'ClientID': '<TODO>',
            'ClientSecret': '<TODO>'})
            
    # ====================================================================================    
    def post(self, msg, image_local_url):
    
        consumer_key=self.config["Access"]["APIKey"]
        consumer_secret=self.config["Access"]["APISecret"]
        access_token=self.config["Access"]["AccessToken"]
        access_token_secret=self.config["Access"]["AccessSecret"]
        
        # https://docs.tweepy.org/en/stable/client.html
        client_v2 = tweepy.Client(#bearer_token=self.config["Access"]["BearerToken"], 
                           consumer_key=consumer_key, 
                           consumer_secret=consumer_secret, 
                           access_token=access_token, 
                           access_token_secret=access_token_secret)
        if image_local_url and os.path.isfile(image_local_url):
            # https://mohammad-wali-khan.medium.com/image-upload-automation-on-twitter-with-tweepy-and-python-f6dfc5ede4ba
            auth_v1 = tweepy.OAuth1UserHandler(consumer_key, consumer_secret, access_token, access_token_secret)
            api_v1 = tweepy.API(auth_v1, wait_on_rate_limit=True)

            # Uploading the image to Twitter
            media = api_v1.media_upload(image_local_url)
            print(f"media.media_id: {media.media_id}")
            # Forbidden: response = api_v1.update_status(status=msg, media_ids=[media.media_id])
            
            res = client_v2.create_tweet(text=msg, media_ids=[media.media_id])
        else:
            res = client_v2.create_tweet(text=msg)
        print(res)
        tweet_id = res.data["id"]
         
        handle = self.get_handle()
        tweet_link = f"https://x.com/{handle}/status/{tweet_id}"

        # Printing the tweet link for confirmation
        print("Tweeted!\nTweet ID:", tweet_id)
        print("Tweet Link:", tweet_link)
        return tweet_link            
            
    # ====================================================================================    
    def config_filename(self):
        return 'settings_x_%s.ini' % self.hl

# ====================================================================================        
if __name__ == '__main__':
    print("Commented to prevent accidental post")
    #x_en = PostX("en")
    #res = x_en.post(msg='Hello world! I posted this via the API.', image_local_url=None)
    #res = x_en.post(msg='Hello world! I posted this via the Python SDK.',
    #                image_local_url="richTextArea_en1.png")
    #print("Result:", res)
    