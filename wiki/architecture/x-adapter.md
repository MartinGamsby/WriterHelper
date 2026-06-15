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
attached to the media (would need `api_v1.create_media_metadata`). Client construction is
factored into `_clients()` (shared by `post` + `post_thread`); URL building into
`_tweet_url(id)`.

## post_thread() — the reply chain

`post_thread(messages, image_local_url, alt_text) → [url]` posts each message in order,
chaining with `in_reply_to_tweet_id=<previous id>`. The image (if any) is uploaded via v1
and attached to the **first** tweet only. Returns one URL per tweet. Used by
[[publishing]] `_publish_thread`.

## Access tier — pay-per-use enrollment (2026)

X **deprecated the Free API tier** in 2026 (Basic/Pro closed to new signups). v2
`create_tweet` now requires the app to be enrolled in a paid product. An un-enrolled app
fails with **403 `client-forbidden`, `reason: client-not-enrolled`** — the response body
echoes the app's numeric `client_id`. This is a portal/account state, **not** a code or
credential bug: regenerating the API key, secret, or access tokens does nothing.

Fix: **console.x.com → Apps → the app → "move this app" to Pay-Per-Use production**
(the portal moved from developer.x.com to console.x.com). Billing is per-request, no
monthly minimum: ~$0.015/post, ~$0.20 if the post **contains a URL** (the surcharge worth
watching for thread segments that carry a link). Enrollment is **per app** (keyed by the
consumer API key = the `client_id`), so every app must be moved separately.

## One app vs. two accounts — `handle` is cosmetic

Each language is a **distinct X account**: `en` posts as @Martin_Gamsby, `fr` as
@MartinGamsby. The `handle` in `settings_x_<hl>.ini` only formats the result URL
(`_tweet_url`); it does **not** select the posting account. The account is determined by
the **access token** (`accesstoken`/`accesssecret`), bound to whichever X account
authorized the app. So reusing one account's access token with the other's handle posts
to the *original* account (and typically 403s on duplicate text) — no code change can
rebind it. Serving both accounts needs a per-account access token; you may share one
app's consumer keys across both only if each account separately authorized that app
(otherwise each account keeps its own app, enrolled in pay-per-use separately).

## See also
- [[post-base]] · [[bluesky-adapter]] · [[social-publishing]] · [[secrets]]
