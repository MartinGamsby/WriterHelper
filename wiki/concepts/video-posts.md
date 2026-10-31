# Video posts (PLANNED — not yet built)

> **Status: roadmap, nothing implemented.** WriterHelper authors text + image cards
> only today. This page records the agreed direction so it survives across sessions; it
> is the one page that intentionally describes *future* state. Delete or fold into the
> live pages once the feature ships.

## Goal

Generate short **vertical videos** from an article and publish them to **TikTok** (as a
video rather than today's photo post) and **YouTube Shorts**, through the
[[browser-hook]] (Claude in Chrome uploads a local file in TikTok Studio / YouTube
Studio — no developer app).

## Build order (smallest viable first)

1. **PoC — text fades in from black.** The simplest possible clip: take the existing
   grabbed branded card ([[image-card-capture]], the "grab image" surface) and render a
   **very short** video of that text **fading in from black**. No motion beyond the fade.
   Just prove the pipeline: card → video file → queue → post.
2. **Add motion.** Then iterate — scroll the text, pan, timed reveals, etc.
3. **YouTube Shorts.** Add a `PLATFORMS` row (browser route, `media="video"`) + a
   [[link-slots]] publish slot; same video asset.

## What has to change to ship it

- **Produce a video asset.** New capture/encode path alongside `capture.js`'s
  html2canvas JPEG ([[image-card-capture]]). PoC = the card image + a fade-in over a few
  frames, encoded to `video/mp4`, slug-named like the captures.
- **Carry it in the job.** `browser_jobs.create` takes an `image`; add a `video` path
  (absolute) the same way, and a `/chrome-post` recipe step to upload it.
- **Turn the popup gate into a composer.** `media == "video"` currently shows
  `renderUnsupportedVideo` and `publish()` refuses it ([[social-publishing]]); offer a
  "video" mode once the asset exists.

## See also
- [[browser-hook]] — the transport (local upload in the signed-in browser)
- [[image-card-capture]] — the card surface the PoC video is built from
- [[social-publishing]] — the popup, modes, and the video gate
- [[link-slots]] — where a YouTube Shorts slot would be registered
