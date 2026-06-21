# Video posts (PLANNED — not yet built)

> **Status: roadmap, nothing implemented.** WriterHelper authors text + image cards
> only today. This page records the agreed direction so it survives across sessions; it
> is the one page that intentionally describes *future* state. Delete or fold into the
> live pages once the feature ships.

## Goal

Generate short **vertical videos** from an article and publish them to **TikTok**, then
**YouTube Shorts** — both reachable through the existing [[post-bridge-adapter]] (one API
key, no per-platform dev app). This is what unblocks the TikTok slot, which today is a
**video gate** in the publish popup (post by hand, paste the URL — see
[[social-publishing]] "Media requirements").

## Build order (smallest viable first)

1. **PoC — text fades in from black.** The simplest possible clip: take the existing
   grabbed branded card ([[image-card-capture]], the "grab image" surface) and render a
   **very short** video of that text **fading in from black**. No motion beyond the fade.
   Just prove the pipeline: card → video file → attach → post.
2. **Add motion.** Then iterate — scroll the text, pan, timed reveals, etc.
3. **YouTube Shorts.** Once TikTok works, add a YouTube Shorts platform row (post-bridge
   supports it too); same video asset, another `PLATFORMS` entry + [[link-slots]] slot.

## What has to change to ship it

- **Produce a video asset.** New capture/encode path alongside `capture.js`'s
  html2canvas JPEG ([[image-card-capture]]). PoC = the card image + a fade-in over a few
  frames, encoded to `video/mp4`.
- **Wire post-bridge video upload.** The adapter's `_upload_image` currently allows
  JPEG/PNG only, but post-bridge's `create-upload-url` mime enum **already accepts
  `video/mp4` and `video/quicktime`** ([[post-bridge-adapter]] "Media requirements"). The
  upload mechanics (create-upload-url → PUT signed URL → `POST /v1/posts` with the media
  id) are unchanged.
- **Flip TikTok from gate to composer.** Change TikTok's `Platform.media` (`"video"`)
  handling so the popup offers a real video-attach mode instead of `renderUnsupportedVideo`
  ([[social-publishing]]). Same flip later enables YouTube Shorts.

## Dependency note

The immediate, separately-tracked prerequisite is just getting the **post-bridge API
wired and posting** (key + account resolution) for the already-supported text/image
platforms. Video is the step *after* that. Until then this stays a plan only.

## See also
- [[post-bridge-adapter]] — the TikTok/Shorts transport; video mime already allowed
- [[image-card-capture]] — the card surface the PoC video is built from
- [[social-publishing]] — the popup, modes, and the current TikTok video gate
- [[link-slots]] — where a YouTube Shorts / TikTok publish slot is registered
