---
name: llm-wiki
description: Maintain WriterHelper's Karpathy-style LLM wiki in wiki/ — ingest new knowledge, query the knowledge base, or lint it for rot. Use when the user says "ingest", "add to the wiki", "what do we know about…", "lint the wiki", or whenever durable project knowledge (a decision, a code contract, a hard-won constraint) is learned and should outlive the session.
---

# LLM Wiki (Karpathy pattern)

The wiki at `wiki/` is an agent-maintained, interlinked markdown knowledge base for
the WriterHelper codebase. You (Claude) own it entirely; the human owns the code and
makes final decisions. Knowledge compounds: every ingest makes future sessions
smarter. Pattern reference:
https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

## Layout

```
wiki/
  index.md          # catalog: every page, one-line summary, grouped by category — read this FIRST
  log.md            # append-only timeline: ## [YYYY-MM-DD] operation | description
  overview.md       # one-screen synthesis of the whole system
  glossary.md       # domain terms (term — meaning), one line each
  concepts/         # cross-cutting design ideas (a pairing rule, a save model, a publish flow)
  architecture/     # the code map — one page per module / format / layer
  sources/          # external properties WriterHelper depends on (the Astro site, platform SDKs)
  entities/         # people, tools, accounts (create the folder when first needed)
  tmp/              # git-ignored session scraps (NOT permanent knowledge)
```

## Conventions

- **Wikilinks**: cross-reference with `[[page-name]]` — the target's filename without
  `.md` and without folder path. Filenames are globally unique kebab-case, so a link
  never needs a path. A link to a not-yet-written page marks future work, not an error.
- One fact-cluster per page; split pages that sprawl past ~250 lines.
- Pages may carry light YAML frontmatter (`tags`, `updated`); keep it optional.
- The wiki describes the **current state** of the system, not a history of changes.
  Update pages in place; never leave "previously X, now Y" changelog prose in a page —
  that belongs in `log.md` or `tmp/`.
- **Code is the source of truth.** If the wiki contradicts the code, fix the wiki and
  flag the disparity to the user. Include concrete code snippets and Mermaid diagrams
  (Mermaid only) where they earn their place.
- Preserve tensions: if two constraints genuinely conflict, record both with a note.

## Workflows

**Ingest** (new durable fact: a decision, a contract, a constraint found the hard way):
1. Take the fact from the code or the conversation.
2. Write/update the relevant page(s) — a single ingest may touch several.
3. Cross-link with `[[wikilinks]]`; add/update the `index.md` entry.
4. Append one `log.md` line (`## [YYYY-MM-DD] ingest | short description`).
Durable = invariants, contracts, rationale, lessons. NOT session trivia (→ `tmp/`).

**Query** ("what do we know about X"):
1. Read `index.md`, open only the relevant pages.
2. Answer with page references. If exploration produced new synthesis worth keeping,
   file it as a page (that's compounding) and log it.

**Lint** (periodic health check):
- Orphan pages (nothing links to them, not in index) → index or merge them.
- Stale claims (a contract that no longer matches the code) → re-verify, update with date.
- Broken wikilinks pointing at pages that should exist by now → write the page or fix the link.
- Contradictions with code → fix the wiki; flag subjective ones to the user.
- Report findings; apply the objective fixes autonomously.

## Session start

Read `wiki/index.md`, `wiki/glossary.md`, and `wiki/overview.md`. Use `index.md` to
locate pages before diving into code — don't bulk-load the whole wiki.
