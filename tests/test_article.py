import os

import filemanager
import rendering


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
def test_save_creates_jekyll_file(fr):
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
    fr.set_title("Un titre accentué")
    fr.set_content("Premier paragraphe.\n\nDeuxième **gras**.")
    fr.set_tags("Gamsblurb,Vie")
    fr.set_excerpt_img("assets/images/test.png")
    fr.set_link("Source", "https://src.example")
    saved = fr.content_md()

    fr.new_article()
    assert fr.title == ""

    assert fr.change_article(saved, "2026-06-10", change_ref=False)
    assert fr.title == "Un titre accentué"
    assert fr.content == "Premier paragraphe.\n\nDeuxième **gras**."
    assert fr.tags == "Gamsblurb,Vie"
    assert fr.excerpt_image == "assets/images/test.png"
    assert fr.get_link("Source") == "https://src.example"
    assert fr.date == "2026-06-10"


def test_change_article_rejects_garbage(fr):
    assert not fr.change_article("no frontmatter here", "2026-06-10")


# ========================================================================================
def test_make_v2_seeds_based_on_link(fr):
    fr.set_title("Original")
    original_url = fr.get_website_url() + "original"
    fr.new_article(copy_current=True)
    assert fr.title == "Original V2"
    assert fr.get_link("Basé sur") == original_url


def test_ref_resolution(pair):
    fr, en = pair.fr(), pair.en()
    fr.set_title("Bonjour")
    en.set_title("Hello")
    assert fr.get_ref() == "https://example.com/en/hello"
    assert en.get_ref() == "https://example.com/fr/bonjour"


# ========================================================================================
def test_hashtags_skip_gamsblurb_and_accents(fr):
    assert rendering.hashtags("Gamsblurb,Vie en société") == "\n#vieensociete"


def test_translate_refuses_nonempty_destination(pair):
    pair.en().set_content("already there")
    assert pair.translate("fr") is False
