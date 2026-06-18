# Popularity tracking

How we measure the *reception* of published posts across socials and watch it over time.
WriterHelper already records *where* each article was posted in its footer [[link-slots]];
this turns those links into engagement numbers and keeps a dated history.

## Shape

- **`popularity.py`** — the pure, tested spine: enumerate readable links, store readings,
  summarize movers. No GUI, no Astro writes.
- **`/popularity` skill** (`.claude/skills/popularity/SKILL.md`) — the agent playbook that
  actually reads numbers off live pages and records them. **Operator-triggered** (run it
  ≈monthly); it is *not* unattended — the browser reads need the operator's logged-in local
  Chrome, which a scheduled cloud agent can't reach.
- **`popularity.json`** — the append-only ledger, in the **WriterHelper repo root**
  (NOT the martingamsby.com checkout, NOT the wiki). One dated snapshot per run.

## Worklist (what gets read)

`collect_worklist(fr, en)` walks every `.md` in the configured posts folders
(`settings_{fr,en}.ini`, same resolution as [[tag-migration]]'s `migrate_tags.py`) and,
reusing the [[serializers]] footer parser, yields one row per **engagement slot** that
holds an **http(s) URL**: `{key, hl, title, date, platform, url}`.

- `ENGAGEMENT_PLATFORMS` mirrors `webapi.LINK_SLOTS` **minus** the reference slots
  (`Source`, `Based on`/`Basé sur`) — those point at someone else's page, not our post.
- Legacy multi-line Bluesky slots hold post *text*, not a link ([[link-slots]]); they
  fail the URL test and are skipped (nothing to visit).
- `key` is the article's `translationKey` (falls back to the filename stem), so a FR/EN
  twin's two posts on the same platform stay distinct (`key` + `hl` + `platform`).

The current back-catalog is ~470 readable links (X/Twitter ≫ Typeshare ≈ Bluesky ≫ the
rest). Too many for one sitting, so `worklist --platform … --hl …` **chunks** a run and
the sweep is **resumable**: re-recording on the same date merges by `(key, hl, platform)`,
overwriting a post's earlier reading rather than duplicating it.

## Reading the numbers

- **Bluesky is scripted** — `bsky_metrics(url)` resolves the handle→DID via the public
  AppView (`public.api.bsky.app`, no auth, no key — `requests` only) and reads
  like/repost/reply/quote counts off `getPostThread`. Reliable, no browser.
- **Everything else is browser-read** through the Claude-for-Chrome MCP using the
  operator's sessions (X likes/reposts/views, Medium claps, YouTube views, …). A number
  that's hidden/private/login-walled is a **gap**, never recorded as 0.
- **X/Twitter is read deterministically, not by eyeballing.** `get_page_text` doesn't
  surface the engagement bar and the visible UI rounds counts; instead a `javascript_tool`
  snippet reads the **exact, un-abbreviated** numbers off X's `aria-label`s (per-button
  `data-testid` labels, with the action-bar `role="group"` label as fallback for views and
  for high-engagement posts where the bookmark-button label format changes). The snippet
  self-polls for hydration so many `navigate`→extract pairs can be chained in one
  `browser_batch`. **`views` is the primary X signal.** An `no-article` result means the
  post was deleted ("this page doesn't exist") → a gap. The exact snippet lives in the
  `/popularity` SKILL.md.
  - **Reply trap (learned the hard way):** when a recorded link is a *reply* to someone
    else's tweet, X renders the parent post above it; reading the first `<article>` grabs
    the parent's (often much larger) counts. The extractor must pick the article whose
    permalink matches the **status ID in the URL**. Symptom: an out-of-character viral
    number on what is actually a reply.

## Ledger & summary

`popularity.json` = `{"snapshots": [{"date": "YYYY-MM-DD", "readings": [...]}]}`, snapshots
kept date-sorted. A reading is `{key, hl, platform, url, title?, metrics:{…}}`; `metrics`
is a free dict so each platform records whatever it surfaces. `summarize()` ranks the
latest snapshot by each platform's `PRIMARY_METRIC` (sum-of-values fallback) and computes
the Δ vs the previous snapshot per `(key, hl, platform)`; `format_summary()` renders the
operator readout. **Append-only**: past snapshots are never edited — they are the history.

## Invariants

- Never fabricate a metric; a missing read is a gap.
- Never write into the Astro post files or the wiki — this is WriterHelper-side telemetry.
- The ledger is append-only; trends depend on past snapshots staying untouched.

## See also
- [[link-slots]] — the footer slots that supply the URLs · [[serializers]] — the footer parser reused
- [[webapi-bridge]] — `LINK_SLOTS` (the slot registry mirrored here) · [[social-publishing]]
