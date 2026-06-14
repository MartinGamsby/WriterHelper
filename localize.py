# Bridge to the site's image hook. When a post's preview image is set to a remote
# URL, martingamsby.com self-hosts it (download + two webp sizes) via
# `tools/localize-images.mjs --file <post.md>`; this module runs that hook and
# reads the rewritten `image:` / `imageThumb:` back so the model can store the
# local paths instead of the hot-linked URL.
import base64
import mimetypes
import os
import re
import subprocess

TOOL_REL = os.path.join("tools", "localize-images.mjs")

# mimetypes misses some image types on Windows (notably webp/avif), so fill the
# gaps; the label is cosmetic (sharp sniffs the bytes) but keep it honest.
_EXT_MIME = {".webp": "image/webp", ".avif": "image/avif", ".bmp": "image/bmp"}


def file_to_data_url(path):
    """Read a local image off disk and return it as a `data:` URL.

    The whole point: a data URL is already a first-class `is_remote` value, so
    feeding it to `ArticleModel.set_excerpt_img` runs it through the exact same
    self-hosting pipeline as a pasted remote URL — the site hook downloads it
    (here, decodes it) into the slug-named `…header.webp` / `…thumb.webp`. That
    lets a dropped/opened file reuse 100% of the existing path with no new mode."""
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        mime = _EXT_MIME.get(os.path.splitext(path)[1].lower())
    if not mime or not mime.startswith("image/"):
        mime = "application/octet-stream"
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    return "data:%s;base64,%s" % (mime, data)


def is_remote(src):
    """True for values the hook should download (http/https, protocol-relative,
    data:). Local paths like `assets/img/x.png` or `/assets/posts/...` are left
    alone."""
    src = src or ""
    return bool(re.match(r"^(https?:)?//", src)) or src.startswith("data:")


def _find_repo_root(start):
    """Walk up from `start` until a folder containing tools/localize-images.mjs is
    found (the martingamsby.com checkout). Returns the path or None."""
    cur = os.path.abspath(start)
    while True:
        if os.path.isfile(os.path.join(cur, TOOL_REL)):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def _read_image_lines(md_path):
    """Read `image:` and `imageThumb:` out of a post's frontmatter."""
    with open(md_path, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^\s*---\s*\n(.*?)\n---\s*\n", text, re.S)
    block = m.group(1) if m else text

    def grab(key):
        mm = re.search(r"^%s:[ \t]*(.+?)[ \t]*$" % key, block, re.M)
        return mm.group(1).strip().strip("\"'") if mm else ""

    return grab("image"), grab("imageThumb")


def localize_file(md_path, timeout=120):
    """Run the site hook on one post file, then return its (image, imageThumb).

    Best-effort: if node, the tool, or the download is unavailable the post keeps
    its remote `image:` (still renders) and this returns (None, None)."""
    root = _find_repo_root(os.path.dirname(md_path))
    if not root:
        print("localize: %s not found above %s" % (TOOL_REL, md_path))
        return None, None
    try:
        subprocess.run(
            ["node", TOOL_REL, "--file", os.path.abspath(md_path)],
            cwd=root, check=True, capture_output=True, text=True, timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as err:
        print("localize: hook failed (%s); leaving remote image" % err)
        return None, None
    return _read_image_lines(md_path)
