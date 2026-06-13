# Post-file serializers. Astro is the WRITTEN format (martingamsby.com); Jekyll
# is kept on the LOAD path only, so legacy .md posts stay openable forever.
# The written layout mirrors templates/post_astro.md.
import os
import re

import yaml

import rendering

DEFAULT_TAGS = "Gamsblurb"
FACETS = ["dev", "physics", "fiction", "music", "ideas"]

_LINK_RE = r'\[([^\[]+)]\(\s*(http[s]?://.+)\s*\)'


# ========================================================================================
# Write (Astro only)
# ========================================================================================
def serialize(article) -> str:
    """The Astro markdown file: frontmatter + body (NO title heading — the site
    layout renders the title) + optional footer links block."""
    fm = [
        "---",
        'title: "%s"' % article.title,
        "date: %s" % article.date,
        "translationKey: %s" % article.get_translation_key(),
        "facets: [%s]" % ", ".join(article.facets),
        "tags: [%s]" % article.get_tags(),
    ]
    if article.draft:
        fm.append("draft: true")          # omitted when publishing
    if article.excerpt_image:
        fm.append("image: %s" % article.excerpt_image)
        # Self-hosted images carry a small list-thumbnail alongside the header
        # (see localize.py); keep it so editing a post never strips it.
        if getattr(article, "image_thumb", ""):
            fm.append("imageThumb: %s" % article.image_thumb)
    fm.append("---")

    out = "\n".join(fm) + "\n\n" + article.content.strip() + "\n"
    footer = rendering.footer_md(article)
    if footer.strip():
        out += "\n---\n\n" + footer
    return out


# ========================================================================================
# Load (format auto-detected)
# ========================================================================================
def parse(article, text, old_date, change_ref=True) -> bool:
    """Load `text` into `article`. Detects Jekyll vs Astro frontmatter and routes
    accordingly. Same mutation contract as the old change_article: delete_last is
    forced off during the load and the model is re-saved (in the Astro format) at
    the end."""
    header = _frontmatter(text)
    if header is None:
        print("Couldn't parse the md file")
        return False

    article.delete_last = False
    article.date = old_date

    if header.get("layout") == "post" or "ref" in header:
        _load_jekyll(article, text, header, change_ref)
    else:
        _load_astro(article, text, header, change_ref)

    article.updated()
    article.delete_last = True
    return True


def _frontmatter(text):
    """Parse just the YAML frontmatter block (first `---` … `---`). Returns a dict
    or None when the file has no parseable frontmatter."""
    m = re.match(r'^\s*---\s*\n(.*?)\n---\s*\n', text, re.S)
    if not m:
        return None
    raw = m.group(1).replace("[,Gamsblurb]", "[Gamsblurb]")
    try:
        data = yaml.full_load(raw)
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def _load_footer(article, footer_text):
    article.links = []
    if footer_text:
        for name, url in re.findall(_LINK_RE, footer_text):
            article.set_link(name, url)


# ---- Jekyll (legacy posts; behavior preserved verbatim) --------------------------------
def _load_jekyll(article, text, header, change_ref):
    parts = text.split("---")
    content = parts[2].strip()

    article.title = header["title"]
    article.content = content.replace("### **%s**" % article.title, "").strip()
    article.excerpt_image = header["excerpt_image"] \
        if ("excerpt_image" in header and header["excerpt_image"]) else ""
    article.image_thumb = ""   # Jekyll posts have no self-hosted thumbnail
    article.determine_length_category()
    article.tags = ",".join(map(str, header["tags"])) if "tags" in header else DEFAULT_TAGS
    article.facets = []
    article.draft = False
    article.translation_key = ""   # Jekyll has none; a key is generated on first save

    _load_footer(article, parts[3] if len(parts) == 4 else "")

    if change_ref:
        _resolve_jekyll_ref(article, header)


def _resolve_jekyll_ref(article, header):
    ref = article.ref
    reference = header.get("ref", "")
    potential = article.date + "-" + reference.replace(ref.get_website_url(), "") + ".md"
    full = os.path.join(ref.get_posts_folder(), potential)
    if os.path.isfile(full):
        with open(full, mode="r", encoding="utf-8") as f:
            ref.change_article(f.read(), os.path.basename(full)[:10], change_ref=False)
    else:
        ref.new_article()


# ---- Astro -----------------------------------------------------------------------------
def _load_astro(article, text, header, change_ref):
    body, footer = _astro_body_footer(text)

    article.title = header["title"]
    # No title heading expected in Astro bodies; strip defensively just in case.
    article.content = body.replace("### **%s**" % article.title, "").strip()
    article.excerpt_image = header["image"] \
        if ("image" in header and header["image"]) else ""
    article.image_thumb = header["imageThumb"] \
        if ("imageThumb" in header and header["imageThumb"]) else ""
    article.determine_length_category()
    tags = header.get("tags") or []
    article.tags = ",".join(map(str, tags)) if tags else DEFAULT_TAGS
    article.facets = [str(f) for f in (header.get("facets") or [])]
    article.draft = bool(header.get("draft", False))
    article.translation_key = str(header.get("translationKey") or "")

    _load_footer(article, footer)

    if change_ref:
        _resolve_astro_twin(article)


def _astro_body_footer(text):
    """Split an Astro file into (body, footer) after the frontmatter. The footer is
    whatever follows the LAST `\\n---\\n` separator, so a horizontal rule inside the
    body does not get mistaken for the footer boundary."""
    m = re.match(r'^\s*---\s*\n.*?\n---\s*\n(.*)$', text, re.S)
    rest = m.group(1) if m else ""
    idx = rest.rfind("\n---\n")
    if idx != -1:
        return rest[:idx], rest[idx + 5:]
    return rest, ""


def _resolve_astro_twin(article):
    """Load the paired-language file (matching translationKey) into `ref`, and
    self-heal a drifted key so the pair re-links. Replaces Jekyll's ref-URL
    derivation."""
    ref = article.ref
    key = article.translation_key
    found = _find_twin_file(ref.get_posts_folder(), key) if key else None
    if not found:
        ref.new_article()
        return
    path, txt = found
    ref.change_article(txt, os.path.basename(path)[:10], change_ref=False)
    # Heal: if the twin's own translationKey drifted from the shared key (legacy data
    # where FR/EN were keyed to each other's slug), rewrite it to match so both files
    # — and the live site — link. No-op once the pair already agrees.
    if ref.translation_key != key:
        ref.translation_key = key
        ref.updated()


def _find_twin_file(folder, key):
    """Locate the twin post for `key`.

    By the Astro convention a pair's translationKey IS the EN file's stem, carried in
    BOTH languages' frontmatter, so a file literally named `<key>.md` is the twin —
    trust the filename (O(1)) even if its own translationKey line has drifted (the
    caller heals it after load). Fall back to a header-only scan for the rarer cases
    where the filename ≠ key (a title renamed after the key froze, or an FR-derived
    key), reading just each post's YAML header rather than the whole file."""
    if not os.path.isdir(folder):
        return None
    direct = os.path.join(folder, key + ".md")
    if os.path.isfile(direct):
        with open(direct, mode="r", encoding="utf-8") as fh:
            return direct, fh.read()
    return _scan_for_key(folder, key)


def _scan_for_key(folder, key):
    """Fallback: frontmatter-only scan of the folder for a matching translationKey."""
    for f in sorted(os.listdir(folder)):
        if not f.endswith(".md"):
            continue
        path = os.path.join(folder, f)
        if _header_has_key(path, key):
            with open(path, mode="r", encoding="utf-8") as fh:
                return path, fh.read()
    return None


def _header_has_key(path, key):
    """True if the post's frontmatter has `translationKey: <key>`. Reads ONLY the
    YAML header (stops at the closing `---`) so large post bodies are never read
    during a folder scan."""
    needle = "translationKey: %s" % key
    seen_open = False
    try:
        with open(path, mode="r", encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if stripped == needle:
                    return True
                if stripped == "---":
                    if seen_open:
                        return False        # closed frontmatter, no match
                    seen_open = True
                elif stripped and not seen_open:
                    return False            # content before any frontmatter
    except OSError:
        return False
    return False
