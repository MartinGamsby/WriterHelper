# Posting — Summary

Per-platform social-media adapters. Each is a thin Python wrapper around the platform's SDK or REST API, configured via a gitignored `[Access]` INI.

```mermaid
graph TD
    AM[ArticleModel.post helper] --> PB[PostBsky]
    AM --> PX[PostX]
    AM -. not wired .-> PFB[PostFB]
    AM -. broken .-> PLI[post_linkedin.py]
    PB --> ATPROTO[atproto.Client]
    PX --> TWEEPY[tweepy v1 + v2]
    PFB --> GRAPH[Facebook Graph v18]
    classDef broken stroke:#f33,stroke-width:2px;
    classDef inactive stroke:#aa3,stroke-dasharray: 5 5;
    class PLI broken
    class PFB inactive
```

## Status by platform

| File | Class | Inherits Post? | Wired into UI? | Notes |
|---|---|---|---|---|
| `post_bsky.py` | `PostBsky` | ✅ | ✅ | Click Bluesky link label → `post_bluesky()` |
| `post_x.py` | `PostX` | ✅ | ✅ | Click X/Twitter link label → `post_x()` |
| `post_fb.py` | `PostFB` | ❌ | ❌ | Older API; no UI hook |
| `post_linkedin.py` | none (broken) | n/a | ❌ | Unindented snippet; do NOT import |

## Routing

Triggered from `ArticleModel.post(name, poster, max_length)` (see [../model/post-routing.md](../model/post-routing.md)). The helper picks text-vs-image based on rendered plain-text length vs the platform `max_length`, then:
1. Calls `poster.post(msg, image_local_url, alt_text)` and gets a URL back.
2. Saves the URL as a `Link` under `name` — which re-saves the `.md` file's footer.
3. Opens the URL in the system browser via `QDesktopServices.openUrl`.

## Files in this folder
- [post-base.md](post-base.md) — `Post` base class, INI shape, override pattern
- [bluesky.md](bluesky.md) — atproto.Client; text or send_image
- [x.md](x.md) — tweepy v1+v2 (v1 needed for media upload)
- [facebook.md](facebook.md) — Graph v18 token+page_id; not in UI flow
- [linkedin.md](linkedin.md) — BROKEN, hardcoded tokens, do not import

## See also
- [../model/post-routing.md](../model/post-routing.md)
- [../practices.md](../practices.md)
