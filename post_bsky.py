import os
from atproto import Client, models
from post import Post

# ====================================================================================
class PostBsky(Post):

    # ====================================================================================
    def __init__(self, hl):
        Post.__init__(self, hl, access={'Handle': '<TODO>', 'AppPassword': '<TODO>'})

    # ====================================================================================
    def _post_url(self, uri):
        # uri e.g. at://did:plc:.../app.bsky.feed.post/3ls52v3vmiy2p -> the web URL.
        id = uri[uri.rfind("/") + 1:]
        return f"https://bsky.app/profile/{self.get_handle()}/post/{id}"

    # ====================================================================================
    def _send(self, client, msg, image_local_url, alt_text, reply_to):
        """One post (optionally with an image, optionally a reply). Returns the SDK
        response (carries .uri/.cid for building the next reply ref)."""
        if image_local_url and os.path.isfile(image_local_url):
            with open(image_local_url, 'rb') as f:
                return client.send_image(text=msg, image=f.read(), image_alt=alt_text,
                                         langs=[self.hl], reply_to=reply_to)
        return client.send_post(msg, langs=[self.hl], reply_to=reply_to)

    # ====================================================================================
    def post(self, msg, image_local_url, alt_text):
        client = Client()
        client.login(self.get_handle(), self.get_app_password())
        # More than text here: https://docs.bsky.app/docs/tutorials/creating-a-post
        post = self._send(client, msg, image_local_url, alt_text, reply_to=None)
        return self._post_url(post.uri)

    # ====================================================================================
    def post_thread(self, messages, image_local_url, alt_text):
        client = Client()
        client.login(self.get_handle(), self.get_app_password())
        urls, root, parent = [], None, None
        for idx, msg in enumerate(messages):
            # Every reply references the thread root + its immediate parent.
            reply_to = None
            if root is not None:
                reply_to = models.AppBskyFeedPost.ReplyRef(root=root, parent=parent)
            img = image_local_url if idx == 0 else None
            resp = self._send(client, msg, img, alt_text, reply_to)
            ref = models.create_strong_ref(resp)
            if root is None:
                root = ref
            parent = ref
            urls.append(self._post_url(resp.uri))
        return urls

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
