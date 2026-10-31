# martingamsby.com (the Astro site)

The external property WriterHelper authors for. A single bilingual personal site (Astro
5 + content collections, GitHub Pages, apex domain **martingamsby.com**) that replaced
two separate Jekyll blogs and a dead WordPress site. Sibling checkout at
`C:\Users\Martin\Documents\GitHub\martingamsby.com`.

WriterHelper is its **deterministic authoring app**: it writes the FR/EN `.md` pair
directly into `src/content/blog/{fr,en}/` ([[file-storage]], [[astro-format]]). The
operator commits + pushes; every push to `main` deploys via GitHub Actions.

## The contract (what the site expects)

- **Doors are lenses, not silos.** All content is one pool tagged by **facet**
  (`dev | physics | fiction | music | ideas`); the homepage doors *filter* it. This is
  why WriterHelper makes [[glossary]] facets mandatory and keeps `serializers.FACETS` in
  lock-step with the site's `content.config.ts` zod enum.
- **Every page knows its twin.** FR/EN are mirrored `/fr/…` `/en/…` routes; the language
  toggle lands on the equivalent page, paired by `translationKey` frontmatter — the key
  WriterHelper mints and freezes ([[bilingual-pairing]]).
- **Frontmatter schema** (zod-enforced site-side): `title`, `date`, `translationKey`,
  `facets[]`, `tags[]`, optional `draft`, optional `image`/`imageThumb`. The zod schema
  still allows `facets: []` (the back-catalog has many), so WriterHelper's ≥1 rule is
  authoring-side only.
- **French is Quebec French** in Martin's colloquial voice; migration preserved post
  bodies byte-for-byte apart from frontmatter ([[machine-translation]] output is meant to
  be hand-proofed).

## Image self-hosting hook

Post images must be **self-hosted, never hot-linked**. The site owns
`tools/localize-images.mjs`, which downloads an external `image:` into two webp
derivatives (`public/assets/posts/<slug>.{header,thumb}.webp`) and rewrites the post
frontmatter to `image:` + `imageThumb:`. WriterHelper invokes it per post via its
`localize.py` hook — see [[astro-format]]. Run modes: no-arg backfill, or
`--file <post.md>` for one post.

## URLs

WriterHelper's `[URLs] website` is the Astro base `https://martingamsby.com/<hl>/blog/`;
`get_post_url()` and the social/"Based on" links share it ([[article-model]]).

## See also
- [[file-storage]] · [[astro-format]] · [[bilingual-pairing]] · [[overview]]
