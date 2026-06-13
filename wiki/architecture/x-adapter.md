# X / Twitter adapter (`post_x.PostX`)

Inherits [[post-base]]. Uses `tweepy` — both v2 (`tweepy.Client`) and v1 (`tweepy.API`).
Limit 280 chars, one image per tweet.

## Config

`settings_x_<hl>.ini` — `[Access]` with `handle`, `apikey`, `apisecret`, `bearertoken`,
`accesstoken`, `accesssecret`, `clientid`, `clientsecret`. Git-ignored, see [[secrets]].
Many fields because v1 media upload uses OAuth1 (consumer/access pair) while v2 tweet
creation also wants them for user-context auth; `BearerToken`/`ClientID`/`ClientSecret`
are kept for completeness but aren't all used by `post()`.

## post() implementation

```python
def post(self, msg, image_local_url, alt_text):
    consumer_key, consumer_secret = APIKey, APISecret
    access_token, access_secret   = AccessToken, AccessSecret
    client_v2 = tweepy.Client(consumer_key, consumer_secret, access_token, access_secret)
    if image_local_url and os.path.isfile(image_local_url):
        auth_v1 = tweepy.OAuth1UserHandler(consumer_key, consumer_secret, access_token, access_secret)
        api_v1  = tweepy.API(auth_v1, wait_on_rate_limit=True)
        media   = api_v1.media_upload(image_local_url)
        res     = client_v2.create_tweet(text=msg, media_ids=[media.media_id])
    else:
        res = client_v2.create_tweet(text=msg)
    return f"https://x.com/{self.get_handle()}/status/{res.data['id']}"
```

Why the v1+v2 split: v2 `create_tweet` is the supported way to post text + attach
existing media, but v2 has no media-upload endpoint at the free/basic tiers — v1
`media_upload` is still required to get a `media_id`; v1 `update_status` (text+media in
one call) is forbidden at current tiers. `alt_text` is passed through but not currently
attached to the media (would need `api_v1.create_media_metadata`).

## See also
- [[post-base]] · [[bluesky-adapter]] · [[social-publishing]]
