# Jekyll post format (legacy, load-only)

**Legacy.** WriterHelper no longer *writes* Jekyll — it writes [[astro-format]]. This
format survives only so old `.md` posts stay loadable: [[serializers]] `parse`
auto-detects `layout: post` and routes to the Jekyll parser (`_load_jekyll`, moved
verbatim from the old `change_article`).

## Anatomy

```markdown
---
layout: post
title: "Sample Title"
categories: ["Length: Short", "Gamsblurb"]
tags: [tag1,tag2,Gamsblurb]
excerpt_image: assets/img/foo.jpg
ref: https://martingamsby.github.io/sample-title

---

### **Sample Title**

Body markdown here.

---

- [X/Twitter](https://x.com/...)
```

Source template: `templates/post.md` ([[templates]]).

## Field semantics

| Field | Source | Notes |
|---|---|---|
| `layout: post` | literal | the detection marker |
| `title` | `title` | double-quoted |
| `categories` | `categories()` | `[<length-label>, "Gamsblurb"]`; label is per-`hl` |
| `tags` | `get_tags()` | comma string interpolated into `[...]` |
| `excerpt_image` | `excerpt_image` | relative path |
| `ref` | `ref.website_url + ref.slug` | URL of the paired other-language article |
| `### **<TITLE>**` | literal | body heading; stripped on reload to avoid duplication |
| body | `content` | raw markdown |
| footer | `footer_md()` | `- [text](url)` per non-empty link |

## Round-trip (load)

`parts = file_contents.split("---")` → 3 or 4 parts (pre-frontmatter `""`, frontmatter,
body, optional footer). Frontmatter via `yaml.full_load` after a defensive
`replace("[,Gamsblurb]","[Gamsblurb]")` (fixes a historically malformed tag list). Body
stripped of the leading `### **<title>**`. Footer regex-scanned for `[name](url)` →
`Link`s. A `ref` field triggers the reciprocal load: derive
`<old_date>-<ref-without-website>.md` in the other folder, recurse with
`change_ref=False`, else `ref.new_article()`. `delete_last` forced False during load.

## See also
- [[astro-format]] — the current written format
- [[serializers]] · [[file-storage]] · [[bilingual-pairing]]
