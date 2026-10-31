# Instagram (Business/Creator) adapter. Posts ONE image to the IG feed via the
# Graph API's Content Publishing flow (create container -> publish -> resolve
# permalink), returning the public post URL so it can feed the Link slot.
#
# Unlike Facebook/Bluesky/X (which upload a local file), Instagram fetches the image
# from a PUBLIC URL server-side, so post() takes an `image_url`, never a local upload —
# site_push/publishing make that URL public first. Rides the same long-lived Facebook
# Page token: it reuses settings_fb_<hl>.ini, with one extra `IgUserId` field (the IG
# Business account id). Inherits the Post base; no Qt. See [[instagram-adapter]].
import requests

from post import Post
# One Graph API version for both Meta adapters — bump it in post_fb and IG follows.
from post_fb import GRAPH_API_VERSION


# ====================================================================================
class PostIG(Post):

    # ====================================================================================
    def __init__(self, hl):
        # Reuses Facebook's settings file; IgUserId is the extra field (the IG Business
        # account id, NOT the Page id). PageId is unused here but kept so the shared
        # file's defaults round-trip when IG writes the template first.
        Post.__init__(self, hl, access={'PageId': '<TODO>', 'Token': '<TODO>',
                                        'IgUserId': '<TODO>'})

    def get_token(self):
        return self.config["Access"]["Token"]

    def get_ig_user_id(self):
        return self.config["Access"]["IgUserId"]

    # The base __init__ prints get_handle(); IG has no handle, so surface the IG id.
    def get_handle(self):
        return self.get_ig_user_id()

    # Reuse Facebook's settings file (same long-lived Page token + an IgUserId line).
    def config_filename(self):
        return 'settings_fb_%s.ini' % self.hl

    # ====================================================================================
    def _graph_url(self, edge):
        return "https://graph.facebook.com/%s/%s/%s" % (
            GRAPH_API_VERSION, self.get_ig_user_id(), edge)

    def _check(self, payload, r, what):
        """Raise on a Graph `error` payload so publishing.py surfaces it in the popup."""
        if isinstance(payload, dict) and 'error' in payload:
            err = payload['error']
            raise RuntimeError("Instagram Graph API error %s on %s: %s"
                               % (err.get('code'), what, err.get('message', payload)))

    # ====================================================================================
    def post(self, msg, image_local_url=None, alt_text=None, embed_url=None,
             image_url=None):
        """Publish one image to the IG feed. `image_url` MUST be a public URL (IG fetches
        it itself; `image_local_url`/`embed_url` are ignored — IG accepts no local upload
        and no link card). `msg` is the caption. Two Graph calls (create container ->
        publish), then the permalink is resolved for the Link slot. Returns the public
        post URL; raises on a Graph error."""
        if not image_url:
            raise RuntimeError(
                "Instagram needs a public image_url (it fetches the image itself); "
                "push the grabbed JPEG to the site first.")
        token = self.get_token()

        # 1. Create the media container from the public image URL + caption.
        r = requests.post(self._graph_url('media'),
                          data={'image_url': image_url, 'caption': msg or '',
                                'access_token': token})
        payload = r.json()
        self._check(payload, r, 'media (container)')
        creation_id = payload.get('id')
        if not creation_id:
            raise RuntimeError("Instagram returned no container id (HTTP %s): %s"
                               % (r.status_code, payload))

        # 2. Publish the container.
        r2 = requests.post(self._graph_url('media_publish'),
                           data={'creation_id': creation_id, 'access_token': token})
        published = r2.json()
        self._check(published, r2, 'media_publish')
        media_id = published.get('id')
        if not media_id:
            raise RuntimeError("Instagram returned no media id (HTTP %s): %s"
                               % (r2.status_code, published))

        # 3. Resolve the permalink (the public post URL for the Link slot).
        return self._permalink(media_id, token)

    # ====================================================================================
    def _permalink(self, media_id, token):
        r = requests.get(
            "https://graph.facebook.com/%s/%s" % (GRAPH_API_VERSION, media_id),
            params={'fields': 'permalink', 'access_token': token})
        payload = r.json()
        self._check(payload, r, 'permalink')
        permalink = payload.get('permalink')
        if not permalink:
            # Published, but the URL didn't read back — surface the media id so the
            # operator sets the Instagram link by hand (avoids a blind re-post).
            raise RuntimeError(
                "Posted to Instagram (media %s) but couldn't read its permalink; open "
                "Instagram, copy the post URL into the Instagram link to avoid re-posting."
                % media_id)
        return permalink


# ====================================================================================
if __name__ == '__main__':
    print("Commented to prevent accidental post")
    # ig_fr = PostIG("fr")
    # res = ig_fr.post(msg='Test', image_url='https://raw.githubusercontent.com/.../x.jpg')
    # print("Result:", res)
