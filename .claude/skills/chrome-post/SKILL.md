---
name: chrome-post
description: Post WriterHelper's queued social posts (X, LinkedIn, Facebook, Instagram, Threads, Pinterest, TikTok, Medium) from the operator's own signed-in Chrome via Claude in Chrome, then report each post's URL back to WriterHelper. Use when the user runs /chrome-post [job-id], says "post the queued jobs", or a WriterHelper hook command starts this session.
---

# /chrome-post — post queued WriterHelper jobs with Claude in Chrome

WriterHelper's publish popup doesn't call these platforms' APIs. When the operator clicks
**Queue for Claude in Chrome**, it writes a job to `browser_jobs/<id>.json` (in the
WriterHelper folder). This skill posts that job in the operator's real Chrome, where
they're already signed in, then records the post URL so the app links it in the
article's footer. Design notes: `wiki/concepts/browser-hook.md`.

**Clicking Queue in the app is the operator's confirmation.** Post a pending job exactly
as written, without asking again. Stop and ask only in the cases listed under
"Stop and ask" below.

## 0 · Get the jobs

Run these from the WriterHelper folder (the one containing `browser_jobs.py`):

```bash
python browser_jobs.py list            # all pending jobs, JSON (oldest first)
python browser_jobs.py show <id>       # a single job
```

With an argument (`/chrome-post <id>`), handle only that job. Without one, handle every
pending job, one at a time. If nothing is pending, say so and stop.

Job fields: `platform`, `label`, `hl` (fr/en), `compose_url`, `account` (the expected
signed-in handle, `""` = not pinned), `mode` (`text` | `image` | `thread`), `posts`
(a list: one entry, or a thread's segments, posted in order), `title`, `image` (an
absolute local path attached to the **first** post, `""` = none), `alt_text`, `link`
(the article's public URL), `max_length`, plus `board` on Pinterest jobs.

## 1 · Load the browser tools (one ToolSearch)

```
select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__read_page,mcp__claude-in-chrome__find,mcp__claude-in-chrome__form_input,mcp__claude-in-chrome__javascript_tool,mcp__claude-in-chrome__get_page_text,mcp__claude-in-chrome__file_upload,mcp__claude-in-chrome__upload_image,mcp__claude-in-chrome__tabs_close_mcp
```

Some of these may not exist in your extension version. Use whatever loaded. Call
`tabs_context_mcp` first, then work in a **new tab** (`tabs_create_mcp`), never in the
operator's own tabs. Close the tabs you opened when you're done.

## 2 · Post one job

1. **Check the file.** If `image` is set, make sure the file exists. If it's missing,
   `fail` the job with "image file missing — re-grab and re-queue".
2. **Open** `compose_url` and use the platform recipe below.
3. **Check the account.** If `account` is set, confirm Chrome is signed in as that
   handle (look at the profile link/avatar menu). If it's a different account, don't
   switch it yourself: `fail` the job with "signed in as X, expected Y" and tell the
   operator. FR and EN often use different accounts (X: two handles).
4. **Enter the text exactly.** Don't rewrite it, translate it, add hashtags, or
   "improve" it. Line breaks matter. Type it into the composer, or for very long text set
   it with `form_input`. Check the composer's text afterwards. Some editors drop newlines
   or auto-link URLs, which is fine.
5. **Attach the image** (when `image` is set), first post only. Try these in order:
   - **a.** `file_upload` with the absolute `image` path on the composer's
     `<input type="file">` (find it with `find`/`read_page`; it's often hidden behind
     the "photo/media" button).
   - **b.** Clipboard paste: `python browser_jobs.py clip <id>` puts the image on the
     OS clipboard. Then click into the composer and press `ctrl+v` (`cmd+v` on macOS).
     Works on X, LinkedIn, Facebook, Threads.
   - **c.** Ask the operator to attach it by hand. Give the exact path, wait for "done",
     then continue.

   Wait until the preview thumbnail appears before posting. For the alt text, use the
   platform's "Alt"/"Description" field when it's easy to reach, cutting `alt_text` to
   the field's limit. Skip it if it's buried.
6. **Thread** (`mode: thread`, X and Threads only): put `posts[0]` in the first box, then
   use the composer's **+ / "Add post" / "Add to thread"** to add each following segment
   in order. Publish all at once ("Post all").
7. **Publish** with the platform's Post/Share/Publish button. Wait for confirmation.
8. **Find the URL** of the new post (the recipe says where), and check that it's really
   the new post: its text starts like `posts[0]` and it was posted "now" or "1m".
9. **Report back:**

```bash
python browser_jobs.py done <id> "<post url>"
```

If it can't be posted, report why so the popup shows it:

```bash
python browser_jobs.py fail <id> "<short reason>"
```

**Never post twice.** If the post went out but you can't find its URL, don't retry the
post. Ask the operator for the URL, or `fail` with "posted, URL not found — paste it by
hand", so the operator pastes it into the link field. A blind retry double-posts.

## Platform recipes

UIs change. These are starting points, not exact selectors. Read the page.

| platform | compose | notes | where the URL is |
|---|---|---|---|
| **X** | `x.com/compose/post` | 280 chars/post; "+" adds a thread post; media button → file input `input[data-testid="fileInput"]` | the confirmation toast's "View", or the profile (`x.com/<handle>`) → newest post → `x.com/<handle>/status/<id>` |
| **LinkedIn** | `linkedin.com/feed/?shareActive=true` (or "Start a post") | personal profile; media icon → upload → "Next"; 3000 chars | toast "View post", or `linkedin.com/in/me/recent-activity/all/` → newest post's `data-urn="urn:li:activity:<n>"` → `https://www.linkedin.com/feed/update/urn:li:activity:<n>/` |
| **Facebook** | `facebook.com` → "What's on your mind?" | **personal profile** (not a Page); Photo/video → upload; audience: leave as default | profile → newest post → its timestamp link (`facebook.com/<user>/posts/…` or `…/permalink/…`) |
| **Instagram** | `instagram.com` → Create (+) → Post → "Select from computer" | image required: upload `image`, keep original crop, Next → Next → caption = `posts[0]` → Share | profile → newest tile → `instagram.com/p/<code>/` |
| **Threads** | `threads.com` → "What's new?" | 500 chars/post; "Add to thread" for segments; image icon → upload | profile `threads.com/@<handle>` → newest → `threads.com/@<handle>/post/<code>` |
| **Pinterest** | `pinterest.com/pin-creation-tool/` | upload `image`; **Title** = `title` (≤100), **Description** = `posts[0]`, **Link** = `link`; board = `board` (if empty, ask the operator once and suggest pinning it in `settings_publish.ini`) → Publish | "See your Pin" → `pinterest.com/pin/<id>/` |
| **TikTok** | `tiktok.com/tiktokstudio/upload` | **photo post**: upload `image` (choose photo mode if asked); caption = `posts[0]`; Post. If the web uploader rejects images for this account, `fail` with that reason | TikTok Studio → Posts → newest → `tiktok.com/@<handle>/photo/<id>` (or `/video/<id>`) |
| **Medium** | `medium.com/new-story` | title field = `title`; body = `posts[0]` without its first line if that just repeats the title; Publish → (tags optional) → "Publish now" | the published story's URL (`medium.com/@<user>/<slug>-<id>`) |

## Stop and ask (don't push through)

- Not signed in, a login wall, 2FA, or a CAPTCHA. Ask the operator to sign in, then
  continue.
- The wrong account (see step 2.3).
- A browser tool fails 2–3 times on the same step, or a page won't load or respond.
- Anything that would post somewhere other than the job's platform and account, or
  change settings, follow people, or send messages. Never do any of these.
- A browser dialog (confirm/alert) would be triggered. Warn first, because it blocks
  the extension.

## Finish

Summarize per job: platform, language, URL (or why it failed). The WriterHelper popup
(if open) flips to "Posted ✓" within a few seconds. Otherwise the link appears the next
time the article is shown.
