# Instagram adapter — PLANNED (not built yet)

Instagram posting rides Meta's Graph API, so it reuses the **same Page + token plumbing
as [[facebook-adapter]]** (an IG **Business/Creator** account linked to the FB Page).
Not implemented yet — this page captures the design + the two hard constraints so the
next session doesn't re-discover them.

## ⚠️ BIG DISCLAIMER — Instagram MUST be the LAST publish step

Instagram's API is server-side: you give it a **public image URL** and it fetches the
bytes itself, then returns the post URL only *after* publishing. That forces this exact
order, with IG done **after** every other platform:

```
1. Square + Grab the card  → richTextArea_<slug>_<hl>1.jpg (already JPEG, see #1)
2. Push that image to the site repo (see constraint #2 — push only, no deploy needed)
3. Create the IG media container (image_url = the public raw URL) → publish
4. Take the returned IG post URL → write it into the article's Link footer
5. Push the article (now carrying the IG link) to the site
```

Why last: the image must be public **before** step 3, and the IG post URL doesn't exist
**until** step 3 — so the article's final push (step 5) can only happen afterwards. Do FB
/ X / Bluesky first; finish with Instagram.

## Constraint #1 — Instagram only accepts JPEG (now satisfied by the grab)

The Content Publishing API rejects PNG and **WebP** `image_url`s — JPEG only, ≤ 8 MB,
aspect ratio 4:5 → 1.91:1 (square 1:1 is fine). The grab now writes **JPEG** directly
(`richTextArea_<slug>_<hl>1.jpg`, [[image-card-capture]]), so the captured card is a valid
IG source as-is — use the **Square** sizing button before grabbing. (The self-hosted site
image is still **WebP** `<slug>.header.webp` and is *not* IG-valid; use the grabbed card.)
The capture being slug-named is also the guarantee you commit the **right article's**
image, not a stale leftover. Ref:
<https://developers.facebook.com/docs/instagram-platform/content-publishing/>.

## Constraint #2 — the public URL can be a GitHub raw URL (no deploy)

The image does **not** need the built/deployed site. A file is publicly reachable the
moment it's pushed, at
`https://raw.githubusercontent.com/<user>/<repo>/main/<path>` — no GitHub Actions build,
no deploy wait. Works because [[martingamsby-site]]'s repo is public. (If it were ever
private, raw URLs would need auth and this wouldn't work.) So "push the image" means just
commit+push the JPEG, not redeploy the whole site.

## API shape (for when it's built)

1. `POST /{ig-user-id}/media` with `image_url` (the public JPEG) + `caption` → returns a
   **container id**.
2. `POST /{ig-user-id}/media_publish` with `creation_id=<container id>` → returns the
   media id → resolve to the post permalink for the Link slot.

Same long-lived Page token as [[facebook-adapter]]; needs `instagram_basic` +
`instagram_content_publish` and an IG Business/Creator account linked to the Page.

## When built, wire it like the others

Subclass [[post-base]] (`settings_instagram_<hl>.ini` or reuse the FB token), register in
`PLATFORMS` ([[publishing]]), add an `instagram` publish slot ([[link-slots]]). IG always
attaches an image, so it's effectively image-only (no text-only, no thread).

## See also
- [[facebook-adapter]] · [[publishing]] · [[social-publishing]] · [[post-base]]
- [[image-card-capture]] · [[astro-format]] · [[martingamsby-site]]
