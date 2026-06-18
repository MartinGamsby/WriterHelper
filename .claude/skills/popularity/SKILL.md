---
name: popularity
description: Read engagement numbers (likes/reposts/views/claps…) for the blog's social posts and record a dated snapshot. Use when the user says "/popularity", "check the popularity", "how are the posts doing", "update the engagement numbers", or wants the periodic (≈monthly) social-metrics sweep across X, Typeshare, Bluesky, YouTube, Medium, LinkedIn, Facebook, Instagram.
---

# Popularity sweep

Read how the bilingual blog's social posts are performing and append a dated snapshot
to the ledger, so month-over-month trends and "biggest movers" fall out. The pure spine
(enumerate links, store readings, summarize) is `popularity.py` ([[popularity-tracking]]);
this playbook is the part only an agent can do — reading numbers off live pages with the
operator's logged-in browser. Run from the repo root.

## How it works

Every published article records *where* it was posted in its footer link slots
([[link-slots]]). `popularity.py worklist` turns those slots into a JSON list of
`{key, hl, title, date, platform, url}` rows — one per readable post link. You visit each
URL, read its engagement number, and record it. **Bluesky is scripted** (free, no login);
**everything else is read from the browser** via the Claude-for-Chrome MCP using the
operator's sessions.

The full back-catalog is ~470 links, too many for one sitting. **Chunk it by platform**
and record as you go — re-recording on the same day MERGES (overwrites a post's earlier
reading, never duplicates), so the sweep is fully resumable across sessions.

## Preconditions

1. The Claude-for-Chrome extension is connected (`list_connected_browsers`). If not, ask
   the user to connect it — do NOT fall back to pixel clicking.
2. The operator is logged into the platforms being swept (X, Medium, LinkedIn, etc.) in
   that browser. Numbers you can't see logged-out become **gaps**, not zeros.
3. You're in the WriterHelper repo root (the ledger `popularity.json` lives here).

## Steps

### 1 — Scope the run
Decide the chunk with the user (default: highest-signal first — X/Twitter EN, then
Typeshare, then the rest). Get the worklist:

```bash
python popularity.py worklist --platform X/Twitter --hl en     # one chunk
python popularity.py worklist                                  # everything
```
`--platform` and `--hl` are repeatable; omit for all. Each row's `url` is what you open.

### 2 — Read the numbers

**Bluesky — scripted, no browser:**
```bash
python popularity.py bsky <url>      # -> {"likes":N,"reposts":N,"replies":N,"quotes":N}
```

**X/Twitter — deterministic via `javascript_tool` (preferred; do NOT eyeball
`get_page_text`).** X's `get_page_text` does *not* reliably surface the like/repost bar,
and the visible UI rounds ("1.2K"). Instead read X's own `aria-label`s, which carry the
**exact, un-abbreviated** counts. `navigate` to the `url`, then run this self-polling
extractor with `javascript_tool` (it waits for hydration, prefers the per-button labels,
and falls back to the action-bar group label so high-engagement posts — whose `bookmark`
button label format changes — still parse):

**Critical: read the FOCAL tweet, not the first `<article>`.** When the status is a *reply*,
X renders the parent post (someone else's, often with far higher counts) *above* yours, and
`querySelector('article')` would grab the parent. Select the article that links to the
**exact status ID from the URL** instead. (Symptom of getting this wrong: a wildly
out-of-character viral number on what's actually a reply.)

```js
await (async () => {
  const num=(s)=>{if(s==null)return null;const m=String(s).replace(/,/g,'').match(/([\d.]+)\s*([KM]?)/i);if(!m)return null;let v=parseFloat(m[1]);if(/k/i.test(m[2]))v*=1e3;if(/m/i.test(m[2]))v*=1e6;return Math.round(v);};
  const idm=location.pathname.match(/status\/(\d+)/);const id=idm?idm[1]:null;
  const focal=()=>{const arts=[...document.querySelectorAll('article')];if(id){for(const a of arts){if(a.querySelector('a[href*="/status/'+id+'"]'))return a;}}return arts[0]||null;};
  const extract=()=>{const art=focal();if(!art)return{error:'no-article',url:location.href};
    const lbl=(t)=>{const e=art.querySelector('[data-testid="'+t+'"]');return e?num(e.getAttribute('aria-label')):null;};
    const g=art.querySelector('[role="group"][aria-label]');const gl=g?g.getAttribute('aria-label').replace(/,/g,''):'';
    const G=(re)=>{const m=gl.match(re);return m?num(m[1]):null;};const pick=(a,b)=>a!=null?a:b;
    return{url:location.href,replies:pick(lbl('reply'),G(/([\d.]+\s*[KM]?)\s*repl/i)),reposts:pick(lbl('retweet'),G(/([\d.]+\s*[KM]?)\s*repost/i)),likes:pick(lbl('like'),G(/([\d.]+\s*[KM]?)\s*like/i)),bookmarks:pick(lbl('bookmark'),G(/([\d.]+\s*[KM]?)\s*bookmark/i)),views:G(/([\d.]+\s*[KM]?)\s*view/i),raw:gl};};
  for(let i=0;i<40;i++){const art=focal();if(art){const g=art.querySelector('[role="group"][aria-label]');if(g&&/view/i.test(g.getAttribute('aria-label')||''))return extract();}await new Promise(r=>setTimeout(r,150));}
  return extract();
})()
```

Batch it for speed: one `browser_batch` chains many `navigate`→`javascript_tool` pairs in
a single round trip (the self-poll makes the sequencing safe). ~7–10 posts per batch works
well; map each result back to its worklist row by order. **`views` is the primary X signal**
(the operator's known signal is X.com English) — capture it plus likes/reposts/replies and
bookmarks-when-shown. A `{"error":"no-article"}` result usually means the post was
**deleted** (page text reads "this page doesn't exist") — verify with `get_page_text`, then
treat it as a **gap**, not a 0. `twitter.com/user/status/<id>` URLs redirect fine to the
logged-in post.

**Every other platform — Claude-for-Chrome:** `navigate` to the `url`, then
`get_page_text` / `read_page` (use `find` if a count is buried) and grab:

| Platform | metrics to capture |
|---|---|
| X/Twitter | likes, reposts, replies, views (bookmarks if shown) |
| Typeshare | likes / reactions, comments (whatever the post surfaces) |
| YouTube / YouTube Shorts | views, likes, comments |
| Medium | claps, responses |
| LinkedIn | reactions, comments, reposts |
| Facebook | reactions, comments, shares |
| Instagram | likes, comments |

Record only what's actually on the page. If a post is gone, private, behind a login
wall, or the number is hidden, **don't invent a number** — set it aside as a gap.

### 3 — Record readings
Build a JSON array of reading objects (one per post you successfully read) and append it
to today's snapshot. Each reading is the worklist row plus a `metrics` dict:

```json
[
  {"key":"2016-03-01-goldfish","hl":"en","platform":"X/Twitter",
   "url":"https://x.com/...","metrics":{"likes":42,"reposts":5,"replies":3,"views":1200}}
]
```
```bash
python popularity.py record --date <YYYY-MM-DD> --from readings.json   # or pipe via stdin
```
Use the real current date for `--date`. Record incrementally after each chunk — the merge
keeps it safe.

### 4 — Report
```bash
python popularity.py summary
```
Show the operator the ranked readout (top posts + Δ vs the previous snapshot), then call
out: the **biggest movers**, anything notable (their known signal is **X.com English**),
and the **gaps** you couldn't read this run. Suggest the next chunk if the sweep is partial.

## Rules

- **Never fabricate a metric.** A missing number is a gap, reported as such — not a 0.
- **Append-only.** Never edit or delete past snapshots; the ledger is the time series.
- **Don't touch the Astro post files or the wiki.** This is WriterHelper-side telemetry;
  it never writes into the martingamsby.com checkout.
- Honour link safety: these URLs are the operator's own posts, but still verify a URL
  looks like the expected platform before navigating.
