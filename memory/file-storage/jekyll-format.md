# Jekyll Post Format

**Legacy, load-only.** WriterHelper no longer *writes* Jekyll — it writes Astro (see
[astro-format.md](astro-format.md)). This format survives only so old `.md` posts
stay loadable: `serializers.parse` auto-detects `layout: post` and routes to the
Jekyll parser (`serializers._load_jekyll`, moved verbatim from the old
`change_article`).

What a legacy saved `.md` file looks like and how it is parsed back.

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
- [Bluesky](https://bsky.app/...)
```

Source template: `templates/post.md`. See [../templates/summary.md](../templates/summary.md).

## Field semantics

| Field | Source | Notes |
|---|---|---|
| `layout: post` | template literal | unchanging |
| `title` | `ArticleModel.title` | double-quoted |
| `categories` | `categories()` slot | `[<length-category-label>, "Gamsblurb"]`; label is per-`hl` (`"Length: Short"` / `"Longueur: Court"` etc.) |
| `tags` | `get_tags()` | comma-separated string interpolated into `[...]`; not actually YAML-list-safe but tolerated by Jekyll |
| `excerpt_image` | `excerpt_image` | relative path |
| `ref` | `ref.website_url + ref.slug` | URL of the paired other-language article |
| `### **<TITLE>**` | template literal | the body heading; `change_article` strips this on reload to avoid duplication |
| body | `ArticleModel.content` | raw markdown |
| footer | `footer_md()` | one `- [text](url)\n` per non-empty link |

## Filename

`<YYYY-MM-DD>-<slug>.md`. Date and slug derive from `ArticleModel.date` and `get_slug()`. Renaming on title/date change is implicit (write new, delete old — see [summary.md](summary.md)).

## Round-trip (load) via `change_article`

```python
parts = file_contents.split("---")     # 3 or 4 parts
# parts[0] = "" (text before first ---)
# parts[1] = frontmatter (yaml)
# parts[2] = body
# parts[3] = optional footer
```

Frontmatter is parsed by `yaml.full_load` after a defensive `replace("[,Gamsblurb]","[Gamsblurb]")` (fixes a malformed tag list that's been written historically).

Read into the model: `title`, `excerpt_image` (default `""`), `tags` (joined back into comma string; default `"Gamsblurb"`).

Body is stripped of the leading `### **<title>**` heading.

Footer (if present) is regex-scanned for `[name](url)` pairs which become `Link` entries.

`ref` field, if present, triggers the reciprocal-load: derive `<old_date>-<ref-without-website>.md` in the other language's `posts_folder`, recurse into `ref.change_article(..., change_ref=False)` if it exists, else `ref.new_article()`.

`delete_last` is forced False during the load — the model state mutates but the file on disk is not deleted.

## Slug rules

```python
def get_slug(self):
    simple = unidecode(self.title) \
        .replace(".","-").replace(" ","-") \
        .replace("--","-").replace("--","-").replace("--","-").replace("--","-") \
        .lower()
    return re.sub(r'[^a-zA-Z0-9_ \r\n\t\f\v-]+', '', simple).replace("--","-").rstrip("-")
```

- `unidecode` flattens accents (`éé` → `ee`, `François` → `Francois`, `kožušček北亰` → `kozuscekBei...`).
- Repeated `.replace("--","-")` chain handles up to 5 consecutive hyphens after dot/space replacement.
- Trailing `-` trimmed.
- Result is the basis of both the filename and the `<REF>` URL the *other* language model embeds.

## See also
- [summary.md](summary.md)
- [../model/article-model.md](../model/article-model.md)
- [../templates/summary.md](../templates/summary.md)
