# Instagram over the Graph API (transport "api"): image-only, and the image must be
# PUBLIC before the call (Meta fetches it server-side) — so it's two steps: stage the
# grabbed card into the site repo + git-push it, then publish with that URL.
# The default Instagram route is the browser hook instead ([[browser-hook]]), which
# uploads the local card directly. See [[instagram-adapter]]. No Qt.
import os
import webbrowser

import localize
import rendering
import site_push


# ========================================================================================
def image_dest(article):
    """The IG source image's filename inside the site repo (slug + hl, JPEG)."""
    return "%s.%s.jpg" % (article.get_slug(), article.hl)


def stage_image(article, img) -> dict:
    """Step 1: copy the grabbed card `img` into the site repo and git-push it so a
    public URL exists. Returns site_push's `{ok, public_url, log, error}`; the
    public_url is handed back to `publish(... mode="image", {"image_url": url})`."""
    if not os.path.isfile(img):
        return {"ok": False, "public_url": "", "log": [],
                "error": "%s not found — use Square, then Grab the image card first." % img}
    repo = localize.find_repo_root(article.get_posts_folder())
    if not repo:
        return {"ok": False, "public_url": "", "log": [],
                "error": "Couldn't locate the martingamsby.com checkout above %s."
                         % article.get_posts_folder()}
    commit_msg = "IG image: %s (%s)" % (article.get_slug(), article.hl)
    return site_push.stage_and_push_image(repo, img, image_dest(article), commit_msg)


# ========================================================================================
def prepare_extras(article, img, img_exists) -> dict:
    """The API popup's extra fields: can the site repo be found (step 1 pushes there),
    the pushed file's name, whether that image is ALREADY pushed (so a reopened popup
    skips the redundant re-push), and the image actually committed (as a data URL) so
    the operator can catch a stale/changed one. Read-only."""
    repo = localize.find_repo_root(article.get_posts_folder())
    dest = image_dest(article)
    status = (site_push.image_status(repo, dest, img)
              if repo and img_exists else {"pushed": False, "public_url": ""})
    dest_abs = os.path.join(repo, site_push.IG_ASSET_SUBDIR, dest) if repo else ""
    return {
        "ig_repo_found": bool(repo),
        "ig_image_dest": dest,
        "ig_image_pushed": status["pushed"],
        "ig_public_url": status["public_url"],
        "ig_repo_image_data_url": (rendering.data_url(dest_abs)
                                   if dest_abs and os.path.isfile(dest_abs) else ""),
    }


# ========================================================================================
def publish(article, p, caption, opts, on_error) -> dict:
    """Step 2: post the already-public image (`opts["image_url"]` from step 1) +
    `caption`. `on_error(p, exc)` turns an adapter exception into the result dict."""
    image_url = opts.get("image_url")
    if not image_url:
        return {"ok": False, "url": "",
                "error": "Push the Instagram image to the site first (step 1)."}
    if len(caption) > p.max_length:
        return {"ok": False, "url": "",
                "error": "Caption is %d characters; %s allows %d."
                         % (len(caption), p.label, p.max_length)}
    try:
        url = p.make_poster(article.hl).post(msg=caption, image_url=image_url,
                                             alt_text=caption)
    except Exception as exc:  # auth/network failure must reach the UI, not just the console
        return on_error(p, exc)

    article.set_link(p.link_name, url)
    webbrowser.open(url)
    return {"ok": True, "url": url, "error": ""}
