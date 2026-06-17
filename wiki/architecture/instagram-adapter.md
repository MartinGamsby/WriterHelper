# Instagram adapter (`post_ig.PostIG`)

Posts ONE image to an Instagram **Business/Creator** feed via Meta's Graph API Content
Publishing flow. It **rides the same Page plumbing as [[facebook-adapter]]** (the IG
account is linked to the FB Page) and **reuses `settings_fb_<hl>.ini`** — with one extra
`IgUserId` field. Inherits [[post-base]]; registered in `PLATFORMS` ([[publishing]]);
exposed as a Publish button on the **Instagram** [[link-slots]] slot (both languages).

## ⚠️ Instagram MUST be the LAST publish step

Instagram's API is server-side: you give it a **public image URL** and Meta fetches the
bytes itself, returning the post URL only *after* publishing. That forces this order, IG
**after** every other platform:

```
1. Square + Grab the card  → richTextArea_<slug>_<hl>1.jpg (already JPEG, see #1)
2. Push that image to the site repo  → public raw URL (auto, step 1 of the popup; see #2)
3. Create the IG media container (image_url = the raw URL) → publish → permalink
4. Permalink is written into the article's Instagram Link slot
5. Push the article (now carrying the IG link) to the site  ← still by hand
```

Why last: the image must be public **before** step 3, and the IG post URL doesn't exist
**until** step 3 — so the article's final push (step 5) can only happen afterwards. Do FB
/ X / Bluesky first; finish with Instagram.

## The two-step popup (image-only)

IG carries no text/thread modes and no link card, so `js/publish.js` renders it as its
own image-only panel with two explicit, feedback-bearing steps ([[social-publishing]]):

- **Step 1 — Push image** → `webapi.publish_instagram_image` →
  `publishing.stage_instagram_image` → `site_push.stage_and_push_image`. Copies the
  grabbed JPEG into the site repo and **git-pushes just that file**, streaming each git
  step (copied → committed → pushed) into the card and handing back the **public raw
  URL**. Disabled until a card is grabbed and the repo is found.
- **Step 2 — Publish** (unlocked once the URL exists + the caption fits) →
  `publish(hl,"instagram","image",caption,{image_url})` → `PostIG.post`. On success the
  permalink lands in the Instagram slot; the popup reminds the operator to push the post.

Caption defaults to the **full plain text** (≤ **2200**, IG's caption limit), editable.

## Constraint #1 — Instagram only accepts JPEG (satisfied by the grab)

The Content Publishing API rejects PNG and **WebP** `image_url`s — JPEG only, ≤ 8 MB,
aspect ratio 4:5 → 1.91:1 (square 1:1 is fine). The grab writes **JPEG** directly
(`richTextArea_<slug>_<hl>1.jpg`, [[image-card-capture]]), so the captured card is a valid
IG source as-is — use the **Square** sizing button before grabbing. (The self-hosted site
image is **WebP** `<slug>.header.webp` and is *not* IG-valid; use the grabbed card.) The
capture being slug-named is also the guarantee you commit the **right article's** image.
Ref: <https://developers.facebook.com/docs/instagram-platform/content-publishing/>.

## Constraint #2 — the public URL is a GitHub raw URL (no deploy)

The image needs no built/deployed site. `site_push` copies the grabbed JPEG into the
sibling [[martingamsby-site]] checkout at **`public/assets/ig/<slug>.<hl>.jpg`** (located
via `localize.find_repo_root` walking up from the posts folder), commits just that file,
and pushes the branch. The file is then public at
`https://raw.githubusercontent.com/<owner>/<repo>/<branch>/public/assets/ig/<slug>.<hl>.jpg`
— **no GitHub Actions build, no deploy wait** — because the repo is public. The owner/repo
+ branch are **derived from the repo's `origin` remote** (no new config). The push sends
the whole branch, so any other already-committed work goes up too — the popup log makes
that visible. This is the one place WriterHelper writes to git itself (everywhere else the
operator pushes by hand); it's deliberately a distinct, operator-triggered **step**.

## `PostIG.post` — the Graph API calls

`post(msg, image_local_url=None, alt_text=None, embed_url=None, image_url=None)`. IG never
uploads a local file, so `image_url` is **required** (raises if missing);
`image_local_url`/`embed_url` are ignored. Shares `post_fb.GRAPH_API_VERSION` (one version
constant for both Meta adapters).

1. `POST /{ig-user-id}/media` with `image_url` + `caption` → **container id**.
2. `POST /{ig-user-id}/media_publish` with `creation_id=<container id>` → **media id**.
3. `GET /{media-id}?fields=permalink` → the post permalink (the Link slot value).

A Graph `error` payload at any step raises `RuntimeError` (→ [[publishing]]'s try/except →
popup). If the post published but the permalink can't be read back, the error **names the
media id** so the operator sets the Instagram link by hand rather than blindly re-posting.

## Config — reuses `settings_fb_<hl>.ini`

`[Access]` gains `IgUserId` (the IG **Business account** id, *not* the Page id) alongside
the existing `PageId` + long-lived `Token`. The token needs `instagram_basic` +
`instagram_content_publish` (on top of FB's `pages_manage_posts`) and an IG
Business/Creator account linked to the Page. Get the long-lived Page token exactly as in
[[facebook-adapter]]; read `IgUserId` from
`GET /{page-id}?fields=instagram_business_account`. If IG runs against an FB file that
predates the `IgUserId` line, `get_ig_user_id()` returns the `<TODO>` default and the API
call fails clearly — add the line. See [[secrets]].

## Cross-posting to Facebook — don't rely on it (myth)

There is **no API parameter that cross-posts an IG feed photo to the linked Facebook
Page**. The `share_to_feed` flag people cite is **Reels-only** and just controls whether a
Reel also appears in the IG feed — nothing to do with Facebook. The Instagram app's
account-level "Share to Facebook" toggle is unreliable for **API-published** posts (Meta
documents that it may not fire for them). So we post to Facebook **directly**
([[facebook-adapter]]) and to Instagram **directly** — both ride the same Page token.
(Bonus: posting FB directly sends the full article text; an IG caption can't carry a real
clickable link.)

## Tests

`tests/test_post_ig.py` mocks `requests` to assert the container→publish→permalink
sequence (image_url + caption + creation_id), the settings-file reuse, the `image_url`
requirement, and that a Graph error / missing permalink raises. `tests/test_site_push.py`
mocks git to assert remote→slug/branch parsing, the raw-URL build, the
copy+add+commit+push sequence, and the failure / "nothing to commit" paths. Wiring cases
(registry, the `_publish_instagram` guards, `stage_instagram_image`) live in
`tests/test_publishing.py` (`fake_ig` / `FakeIGPoster`).

## See also
- [[facebook-adapter]] · [[publishing]] · [[social-publishing]] · [[post-base]]
- [[image-card-capture]] · [[link-slots]] · [[secrets]] · [[martingamsby-site]]
