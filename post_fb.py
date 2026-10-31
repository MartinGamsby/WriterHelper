# Facebook Page adapter. Posts to a Facebook Page's feed (text) or photos
# (image) via the Graph API, returning the public post URL so it can feed the
# Link slot. Inherits the Post base (msg/image/alt contract); no Qt.
import os

import requests

from post import Post

# Graph API version. Meta retires versions ~2 years after release; bump this
# when posts start returning an "unsupported version" error.
GRAPH_API_VERSION = "v21.0"


# ====================================================================================
class PostFB(Post):

    # ====================================================================================
    def __init__(self, hl):
        # One assignment with BOTH fields — the old code assigned ['Access'] twice,
        # which dropped Token and made get_token() raise. See [[facebook-adapter]].
        Post.__init__(self, hl, access={'PageId': '<TODO>', 'Token': '<TODO>'})

    def get_token(self):
        return self.config["Access"]["Token"]

    def get_page_id(self):
        return self.config["Access"]["PageId"]

    # The base __init__ prints get_handle(); FB has no handle, so surface the page id.
    def get_handle(self):
        return self.get_page_id()

    # ====================================================================================
    def _graph_url(self, edge):
        return "https://graph.facebook.com/%s/%s/%s" % (
            GRAPH_API_VERSION, self.get_page_id(), edge)

    # ====================================================================================
    def post(self, msg, image_local_url, alt_text, embed_url=None):
        """Post to the Page. (embed_url is ignored — Facebook unfurls a link preview
        from the URL in the message text itself.) With an image -> /photos (the local file is uploaded
        as the `source` multipart part, and `alt_text` becomes the photo's custom
        alt text); without -> /feed. Returns the public post URL; raises on a Graph
        API error so publishing.py surfaces it in the popup."""
        if image_local_url and os.path.isfile(image_local_url):
            data = {'message': msg, 'access_token': self.get_token()}
            if alt_text:
                data['alt_text_custom'] = alt_text
            with open(image_local_url, 'rb') as f:
                r = requests.post(self._graph_url('photos'), data=data,
                                  files={'source': f})
        else:
            r = requests.post(self._graph_url('feed'),
                              data={'message': msg, 'access_token': self.get_token()})

        payload = r.json()
        if 'error' in payload:
            err = payload['error']
            raise RuntimeError("Facebook Graph API error %s: %s"
                               % (err.get('code'), err.get('message', payload)))
        # /feed returns {"id": "<page>_<post>"}; /photos returns a photo id plus the
        # feed-post id in "post_id" — that's the one that resolves to the post page.
        post_id = payload.get('post_id') or payload.get('id')
        if not post_id:
            raise RuntimeError("Facebook returned no post id (HTTP %s): %s"
                               % (r.status_code, payload))
        return "https://www.facebook.com/%s" % post_id

    # ====================================================================================
    def config_filename(self):
        return 'settings_fb_%s.ini' % self.hl


# ====================================================================================
if __name__ == '__main__':
    print("Commented to prevent accidental post")
    # fb_fr = PostFB("fr")
    # res = fb_fr.post(msg='Test', image_local_url=None, alt_text='')
    # print("Result:", res)
