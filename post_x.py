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
    def _clients(self):
        """Build the v2 client (tweet creation) + v1 API (media upload). v2 has no
        media-upload endpoint at free/basic tiers, so v1 media_upload is still needed
        to get a media_id; v1 update_status is forbidden at current tiers."""
        a = self.config["Access"]
        consumer_key, consumer_secret = a["APIKey"], a["APISecret"]
        access_token, access_secret = a["AccessToken"], a["AccessSecret"]
        # https://docs.tweepy.org/en/stable/client.html
        client_v2 = tweepy.Client(consumer_key=consumer_key,
                                  consumer_secret=consumer_secret,
                                  access_token=access_token,
                                  access_token_secret=access_secret)
        auth_v1 = tweepy.OAuth1UserHandler(consumer_key, consumer_secret,
                                           access_token, access_secret)
        api_v1 = tweepy.API(auth_v1, wait_on_rate_limit=True)
        return client_v2, api_v1

    # ====================================================================================
    def _tweet_url(self, tweet_id):
        return f"https://x.com/{self.get_handle()}/status/{tweet_id}"

    # ====================================================================================
    def post(self, msg, image_local_url, alt_text):
        client_v2, api_v1 = self._clients()
        if image_local_url and os.path.isfile(image_local_url):
            media = api_v1.media_upload(image_local_url)
            res = client_v2.create_tweet(text=msg, media_ids=[media.media_id])
        else:
            res = client_v2.create_tweet(text=msg)
        return self._tweet_url(res.data["id"])

    # ====================================================================================
    def post_thread(self, messages, image_local_url, alt_text):
        client_v2, api_v1 = self._clients()
        urls, prev_id = [], None
        for idx, msg in enumerate(messages):
            kwargs = {"text": msg}
            if prev_id is not None:
                kwargs["in_reply_to_tweet_id"] = prev_id
            if idx == 0 and image_local_url and os.path.isfile(image_local_url):
                media = api_v1.media_upload(image_local_url)
                kwargs["media_ids"] = [media.media_id]
            res = client_v2.create_tweet(**kwargs)
            prev_id = res.data["id"]
            urls.append(self._tweet_url(prev_id))
        return urls

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
