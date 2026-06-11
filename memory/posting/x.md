# X / Twitter — `post_x.PostX`

Inherits [Post](post-base.md). Uses [`tweepy`](https://www.tweepy.org/) — both v2 (`tweepy.Client`) and v1 (`tweepy.API`).

## Config

`settings_x_<hl>.ini`:

```ini
[Access]
handle = your_handle
apikey = ...
apisecret = ...
bearertoken = ...
accesstoken = ...
accesssecret = ...
clientid = ...
clientsecret = ...
```

Why so many fields: v1 media upload uses OAuth1 (consumer/access pair), while v2 tweet creation also wants those for user-context auth. `BearerToken`, `ClientID`, `ClientSecret` are kept in the INI for completeness/possible OAuth2 paths but aren't all used in the current `post()`.

## post() implementation

```python
def post(self, msg, image_local_url, alt_text):
    consumer_key    = self.config["Access"]["APIKey"]
    consumer_secret = self.config["Access"]["APISecret"]
    access_token    = self.config["Access"]["AccessToken"]
    access_secret   = self.config["Access"]["AccessSecret"]

    client_v2 = tweepy.Client(
        consumer_key=consumer_key, consumer_secret=consumer_secret,
        access_token=access_token, access_token_secret=access_secret)

    if image_local_url and os.path.isfile(image_local_url):
        auth_v1 = tweepy.OAuth1UserHandler(consumer_key, consumer_secret,
                                           access_token, access_secret)
        api_v1 = tweepy.API(auth_v1, wait_on_rate_limit=True)
        media = api_v1.media_upload(image_local_url)
        res = client_v2.create_tweet(text=msg, media_ids=[media.media_id])
    else:
        res = client_v2.create_tweet(text=msg)

    tweet_id = res.data["id"]
    return f"https://x.com/{self.get_handle()}/status/{tweet_id}"
```

Why the v1+v2 split:
- v2 `create_tweet` is the supported way to post text + attach existing media.
- v2 has no media-upload endpoint accessible at the free/basic tiers; the v1 `media_upload` is still required to get a `media_id`.
- v1 `update_status` (text + media in one call) is forbidden at current API tiers — that's why the code splits.

`alt_text` is passed through but not currently attached to the tweet's media (would require an extra `api_v1.create_media_metadata` call).

## Limits

- 280 characters (set as `max_length` in `ArticleModel.post_x`).
- One image per tweet (extending to 4 is possible).

## See also
- [post-base.md](post-base.md)
- [summary.md](summary.md)
- [../model/post-routing.md](../model/post-routing.md)
