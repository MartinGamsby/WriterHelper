import os

import filemanager
import localize
import rendering
import serializers
from articles import ArticlesModel


# ========================================================================================
def test_slug_transliterates_and_kebabs(fr):
    fr.title = "Hello World. Été François"
    assert fr.get_slug() == "hello-world-ete-francois"


def test_slug_strips_specials(fr):
    fr.title = "kožušček 北亰 ! (wow)"
    assert fr.get_slug() == "kozuscek-Bei-Jing-wow".lower()


# ========================================================================================
def test_length_categories(fr):
    fr.set_content("x" * 100)
    assert fr.mini and not fr.medium
    assert fr.get_length_category() == "Longueur: Mini"

    fr.set_content("x" * 500)
    assert not fr.mini and not fr.medium

    fr.set_content("x" * 2500)
    assert fr.medium
    assert fr.get_length_category() == "Longueur: Moyen"


def test_length_category_english(pair):
    en = pair.en()
    en.set_content("x" * 100)
    assert en.get_length_category() == "Length: Mini"


# ========================================================================================
def test_save_creates_post_file(fr):
    fr.set_title("Mon article")
    today = filemanager.ContentFile.get_date_str()
    path = os.path.join(fr.get_posts_folder(), f"{today}-mon-article.md")
    assert os.path.isfile(path)


def test_rename_deletes_previous_file(fr):
    fr.set_title("Premier titre")
    fr.set_title("Deuxième titre")
    today = filemanager.ContentFile.get_date_str()
    files = sorted(os.listdir(fr.get_posts_folder()))
    assert f"{today}-deuxieme-titre.md" in files
    assert f"{today}-premier-titre.md" not in files


def test_new_article_does_not_delete_previous_post(fr):
    """A fresh post is not a rename: starting one and titling it must leave the
    article we left on disk (regression — new_both_articles was deleting it on the
    first keystroke via the stale last_filename)."""
    fr.set_title("Article existant")
    today = filemanager.ContentFile.get_date_str()
    existing = f"{today}-article-existant.md"

    fr.new_article()
    fr.set_title("Nouvel article")

    files = sorted(os.listdir(fr.get_posts_folder()))
    assert existing in files               # the one we left stays put
    assert f"{today}-nouvel-article.md" in files


def test_new_both_articles_does_not_delete_previous_posts(pair):
    """Same guarantee for the FR+EN 'New both articles' path on both columns."""
    fr, en = pair.fr(), pair.en()
    fr.set_title("FR existant")
    en.set_title("EN existing")
    today = filemanager.ContentFile.get_date_str()

    fr.new_both_articles()
    fr.set_title("FR nouveau")
    en.set_title("EN new")

    assert f"{today}-fr-existant.md" in os.listdir(fr.get_posts_folder())
    assert f"{today}-en-existing.md" in os.listdir(en.get_posts_folder())


# ========================================================================================
def test_links_upsert_and_footer(fr):
    fr.set_link("Source", "https://a.example")
    fr.set_link("Bluesky", "https://b.example")
    fr.set_link("Source", "https://c.example")  # replaces, keeps order
    assert fr.get_link("Source") == "https://c.example"
    assert rendering.footer_md(fr) == \
        "- [Source](https://c.example)\n- [Bluesky](https://b.example)\n"
    assert fr.get_link("Nope") == ""


# ========================================================================================
def test_change_article_round_trip(fr):
    fr.set_date("2026-06-10")
    fr.set_title("Un titre accentué")
    fr.set_content("Premier paragraphe.\n\nDeuxième **gras**.")
    fr.set_tags("Gamsblurb,Vie")
    fr.set_excerpt_img("assets/img/test.png")
    fr.set_facets(["dev", "ideas"])
    fr.set_draft(True)
    fr.set_link("Source", "https://src.example")
    saved = fr.content_md()
    key = fr.get_translation_key()

    fr.new_article()
    assert fr.title == ""

    assert fr.change_article(saved, "2026-06-10", change_ref=False)
    assert fr.title == "Un titre accentué"
    assert fr.content == "Premier paragraphe.\n\nDeuxième **gras**."
    assert fr.tags == "Gamsblurb,Vie"
    assert fr.excerpt_image == "assets/img/test.png"   # image: round-trips
    assert fr.facets == ["dev", "ideas"]
    assert fr.draft is True
    assert fr.translation_key == key
    assert fr.get_link("Source") == "https://src.example"
    assert fr.date == "2026-06-10"


def test_astro_serialize_golden(fr):
    fr.set_date("2026-06-13")
    fr.set_title("Un Titre")
    fr.set_content("Corps.")
    fr.set_facets(["dev", "ideas"])
    fr.set_link("X/Twitter", "https://x.com/a")
    assert fr.content_md() == (
        '---\n'
        'title: "Un Titre"\n'
        'date: 2026-06-13\n'
        'translationKey: 2026-06-13-un-titre\n'
        'facets: [dev, ideas]\n'
        'tags: [Gamsblurb]\n'
        '---\n'
        '\n'
        'Corps.\n'
        '\n'
        '---\n'
        '\n'
        '- [X/Twitter](https://x.com/a)\n'
    )


def test_change_article_rejects_garbage(fr):
    assert not fr.change_article("no frontmatter here", "2026-06-10")


def test_legacy_jekyll_load(fr):
    legacy = (
        '---\n'
        'layout: post\n'
        'title: "Vieux Titre"\n'
        'categories: ["Longueur: Court", "Gamsblurb"]\n'
        'tags: [Gamsblurb,Vie]\n'
        'excerpt_image: assets/img/old.png\n'
        'ref: https://martingamsby.github.io/en/old-title\n'
        '\n'
        '---\n'
        '\n'
        '### **Vieux Titre**\n'
        '\n'
        'Le corps.\n'
        '\n'
        '---\n'
        '\n'
        '- [X/Twitter](https://x.com/old)\n'
    )
    assert fr.change_article(legacy, "2026-06-10", change_ref=False)
    assert fr.title == "Vieux Titre"
    assert fr.content == "Le corps."          # title heading stripped
    assert fr.tags == "Gamsblurb,Vie"
    assert fr.excerpt_image == "assets/img/old.png"
    assert fr.facets == []
    assert fr.draft is False
    assert fr.get_link("X/Twitter") == "https://x.com/old"


# ========================================================================================
def test_remote_image_is_localized(fr, monkeypatch):
    # The site hook runs out-of-process; stub it so the test stays offline.
    calls = []

    def fake(md_path, **kwargs):
        calls.append(md_path)
        return "/assets/posts/abc123.header.webp", "/assets/posts/abc123.thumb.webp"

    monkeypatch.setattr(localize, "localize_file", fake)

    fr.set_date("2026-06-13")
    fr.set_title("Un Titre")
    fr.set_excerpt_img("https://blob.example/preview.jpg")

    assert len(calls) == 1                                   # hook fired once
    assert fr.excerpt_image == "/assets/posts/abc123.header.webp"
    assert fr.image_thumb == "/assets/posts/abc123.thumb.webp"
    md = fr.content_md()
    assert "image: /assets/posts/abc123.header.webp\n" in md
    assert "imageThumb: /assets/posts/abc123.thumb.webp\n" in md


def test_local_image_skips_hook(fr, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("hook must not run for local paths")

    monkeypatch.setattr(localize, "localize_file", boom)
    fr.set_excerpt_img("assets/img/test.png")               # already local
    assert fr.excerpt_image == "assets/img/test.png"
    assert fr.image_thumb == ""
    assert "imageThumb:" not in fr.content_md()


def test_failed_data_image_is_dropped_never_persisted(fr, monkeypatch):
    # A dropped/opened image is a data: URL. If the site hook can't self-host it,
    # the raw blob must NOT survive in the post — drop it instead.
    monkeypatch.setattr(localize, "localize_file", lambda *a, **k: (None, None))

    fr.set_date("2026-06-13")
    fr.set_title("Un Titre")
    fr.set_excerpt_img("data:image/png;base64,AAAA" + "B" * 5000)

    assert fr.excerpt_image == ""
    assert fr.image_thumb == ""
    md = fr.content_md()
    assert "data:" not in md                                 # blob never persisted
    # ...and the re-save scrubbed it from disk too.
    on_disk = os.path.join(fr.get_posts_folder(), fr.content_file.last_filename)
    assert "data:" not in open(on_disk, encoding="utf-8").read()


def test_failed_data_image_retries_once(fr, monkeypatch):
    # The hook fails transiently (cold start); the retry should win.
    results = iter([(None, None),
                    ("/assets/posts/x.header.webp", "/assets/posts/x.thumb.webp")])
    calls = []

    def flaky(md_path, **kwargs):
        calls.append(md_path)
        return next(results)

    monkeypatch.setattr(localize, "localize_file", flaky)
    fr.set_date("2026-06-13")
    fr.set_title("Un Titre")
    fr.set_excerpt_img("data:image/png;base64,AAAA")

    assert len(calls) == 2                                   # one retry
    assert fr.excerpt_image == "/assets/posts/x.header.webp"
    assert fr.image_thumb == "/assets/posts/x.thumb.webp"


def test_failed_remote_url_is_left_in_place(fr, monkeypatch):
    # A small http(s) URL that fails to localize is kept (it still renders) — and
    # is NOT retried, unlike a data: blob.
    calls = []

    def fail(md_path, **kwargs):
        calls.append(md_path)
        return None, None

    monkeypatch.setattr(localize, "localize_file", fail)
    fr.set_date("2026-06-13")
    fr.set_title("Un Titre")
    fr.set_excerpt_img("https://blob.example/preview.jpg")

    assert len(calls) == 1                                   # no retry for remote URLs
    assert fr.excerpt_image == "https://blob.example/preview.jpg"


def test_image_thumb_round_trips(fr):
    astro = (
        '---\n'
        'title: "Avec Image"\n'
        'date: 2026-06-13\n'
        'translationKey: 2026-06-13-with-image\n'
        'facets: [ideas]\n'
        'tags: [Gamsblurb]\n'
        'image: /assets/posts/abc123.header.webp\n'
        'imageThumb: /assets/posts/abc123.thumb.webp\n'
        '---\n'
        '\n'
        'Corps.\n'
    )
    assert fr.change_article(astro, "2026-06-13", change_ref=False)
    assert fr.excerpt_image == "/assets/posts/abc123.header.webp"
    assert fr.image_thumb == "/assets/posts/abc123.thumb.webp"
    # Re-serializing must keep the thumbnail line (no strip on edit).
    assert "imageThumb: /assets/posts/abc123.thumb.webp\n" in fr.content_md()


# ========================================================================================
def test_make_v2_seeds_based_on_link(fr):
    fr.set_date("2026-06-13")
    fr.set_title("Original")
    original_url = fr.get_website_url() + "2026-06-13-original/"
    fr.new_article(copy_current=True)
    assert fr.title == "Original V2"
    assert fr.get_link("Basé sur") == original_url


# ========================================================================================
# Astro pairing: sticky translationKey, pair-shared facets/draft, twin-by-key scan.
def test_translation_key_is_english_derived_and_shared(pair):
    fr, en = pair.fr(), pair.en()
    en.set_date("2026-06-13")
    fr.set_date("2026-06-13")
    en.set_title("Hello World")
    fr.set_title("Bonjour Le Monde")
    assert en.get_translation_key() == "2026-06-13-hello-world"
    assert fr.get_translation_key() == "2026-06-13-hello-world"


def test_translation_key_is_sticky_under_title_change(pair):
    fr, en = pair.fr(), pair.en()
    en.set_date("2026-06-13")
    en.set_title("Hello")
    key = en.get_translation_key()
    en.set_title("Hello Renamed")
    en.set_date("2026-07-01")
    assert en.get_translation_key() == key   # filename/URL move, key frozen


def test_facets_and_draft_are_pair_shared(pair):
    fr, en = pair.fr(), pair.en()
    fr.set_facets(["physics"])
    fr.set_draft(True)
    assert en.facets == ["physics"]
    assert en.draft is True


def test_astro_twin_resolved_by_key(pair):
    fr, en = pair.fr(), pair.en()
    en.set_date("2026-06-13")
    fr.set_date("2026-06-13")
    en.set_title("Hello")
    fr.set_title("Bonjour")
    en.set_content("EN body")
    fr.set_content("FR body")

    # Fresh, independent pair on the same folders: loading FR must pull its EN twin.
    fresh = ArticlesModel.create(config_dir=pair.cfg_dir)
    fr_file = os.path.join(fr.get_posts_folder(), "2026-06-13-bonjour.md")
    fresh.fr().load_file(fr_file)
    assert fresh.fr().title == "Bonjour"
    assert fresh.en().title == "Hello"   # twin found via translationKey scan


def test_key_shared_when_french_authored_first(pair):
    """Regression: authoring FR fully BEFORE EN must still leave BOTH files with the
    same translationKey (the old code froze each side independently → no link)."""
    fr, en = pair.fr(), pair.en()
    fr.set_date("2026-06-13")
    en.set_date("2026-06-13")
    fr.set_title("Bonjour Le Monde")     # FR first, EN still untitled
    fr.set_content("Corps.")
    en.set_title("Hello World")          # EN authored afterwards
    en.set_content("Body.")
    assert fr.get_translation_key() == en.get_translation_key()

    # And a fresh pair must re-link them from disk.
    fresh = ArticlesModel.create(config_dir=pair.cfg_dir)
    fresh.fr().load_file(os.path.join(fr.get_posts_folder(),
                                      "2026-06-13-bonjour-le-monde.md"))
    assert fresh.en().title == "Hello World"


def test_retranslate_adopts_existing_pair_key(pair):
    """Clearing one side with new_article() and re-authoring it must re-adopt the
    pair's existing key (so re-translating never breaks an existing link)."""
    fr, en = pair.fr(), pair.en()
    fr.set_date("2026-06-13")
    en.set_date("2026-06-13")
    fr.set_title("Bonjour")
    en.set_title("Hello")
    key = fr.get_translation_key()

    en.new_article()                     # wipe EN to re-translate it
    assert en.translation_key == ""
    en.set_title("Hello Again")
    assert en.get_translation_key() == key
    assert fr.get_translation_key() == key


def test_blank_new_article_writes_no_file(fr):
    """Regression: a title-less article must not litter a stray `<date>-.md`."""
    fr.new_article()
    today = filemanager.ContentFile.get_date_str()
    assert f"{today}-.md" not in os.listdir(fr.get_posts_folder())


def test_loading_heals_swapped_twin_keys(pair):
    """Legacy/corrupted data: FR keyed to the EN slug, EN keyed to the FR slug (each
    points at the other's filename). Loading FR must still find EN — by filename — and
    REWRITE EN's drifted key so both files share it (so the live site links them too)."""
    fr, en = pair.fr(), pair.en()
    en_stem, fr_stem = "2026-06-13-hello", "2026-06-13-bonjour"
    def post(title, key):
        return (f'---\ntitle: "{title}"\ndate: 2026-06-13\n'
                f'translationKey: {key}\nfacets: []\ntags: [Gamsblurb]\n---\n\nbody\n')
    # Write the swapped pair straight to disk.
    with open(os.path.join(fr.get_posts_folder(), fr_stem + ".md"), "w", encoding="utf-8") as f:
        f.write(post("Bonjour", en_stem))      # FR carries the EN slug
    with open(os.path.join(en.get_posts_folder(), en_stem + ".md"), "w", encoding="utf-8") as f:
        f.write(post("Hello", fr_stem))         # EN carries the FR slug (drifted)

    fresh = ArticlesModel.create(config_dir=pair.cfg_dir)
    fresh.fr().load_file(os.path.join(fr.get_posts_folder(), fr_stem + ".md"))
    assert fresh.en().title == "Hello"                       # twin found by filename
    assert fresh.en().translation_key == en_stem             # in-memory healed
    with open(os.path.join(en.get_posts_folder(), en_stem + ".md"), encoding="utf-8") as f:
        assert ("translationKey: " + en_stem) in f.read()    # on-disk healed


def test_twin_resolves_after_title_rename(pair):
    """When a title is renamed AFTER the key froze, the twin file's name no longer
    equals the key, so resolution must fall back to the frontmatter scan."""
    fr, en = pair.fr(), pair.en()
    fr.set_date("2026-06-13")
    en.set_date("2026-06-13")
    en.set_title("Hello")
    fr.set_title("Bonjour")
    en.set_title("Hello Renamed")        # EN file now 2026-06-13-hello-renamed.md,
    fr.set_content("corps")              #   but key stays 2026-06-13-hello

    fresh = ArticlesModel.create(config_dir=pair.cfg_dir)
    fresh.fr().load_file(os.path.join(fr.get_posts_folder(), "2026-06-13-bonjour.md"))
    assert fresh.en().title == "Hello Renamed"


# ========================================================================================
def test_hashtags_skip_gamsblurb_and_accents(fr):
    assert rendering.hashtags("Gamsblurb,Vie en société") == "\n#vieensociete"


def test_translate_refuses_nonempty_destination(pair):
    pair.en().set_content("already there")
    assert pair.translate("fr") is False
