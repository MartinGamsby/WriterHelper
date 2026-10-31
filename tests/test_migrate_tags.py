import migrate_tags


# ========================================================================================
# plan_pair: normalize + union across the twin
def test_plan_pair_normalizes_each_side():
    new_en, new_fr = migrate_tags.plan_pair(
        en_tags=["Heatlh", "Learn", "Gamsblurb"],
        fr_tags=["santé", "Apprendre", "Gamsblur"])
    assert new_en == ["Health", "Learning", "Gamsblurb"]
    assert new_fr == ["Santé", "Apprentissage", "Gamsblurb"]


def test_plan_pair_unions_vocab_concepts_both_ways():
    # EN has Motivation that FR lacks; FR has Piano that EN lacks -> both end matched.
    new_en, new_fr = migrate_tags.plan_pair(
        en_tags=["Health", "Motivation", "Gamsblurb"],
        fr_tags=["Santé", "Piano", "Gamsblurb"])
    assert set(new_en) == {"Health", "Motivation", "Piano", "Gamsblurb"}
    assert set(new_fr) == {"Santé", "Motivation", "Piano", "Gamsblurb"}


def test_plan_pair_keeps_one_off_tags_on_their_own_side():
    new_en, new_fr = migrate_tags.plan_pair(
        en_tags=["Health", "Some Custom Thing", "Gamsblurb"],
        fr_tags=["Santé", "Gamsblurb"])
    assert "Some Custom Thing" in new_en       # non-vocabulary one-off stays on EN
    assert "Some Custom Thing" not in new_fr   # NOT forced onto the twin


def test_plan_pair_fixes_cross_language_leak():
    # A French physics tag sitting in the EN file becomes its English label.
    new_en, _ = migrate_tags.plan_pair(en_tags=["Astrophysique", "Trou Noir"], fr_tags=[])
    assert "Astrophysics" in new_en and "Black Hole" in new_en
    assert "Astrophysique" not in new_en


def test_house_tag_present_once_and_last_on_normal_posts():
    new_en, new_fr = migrate_tags.plan_pair(en_tags=["Health"], fr_tags=["Santé"])
    assert new_en[-1] == "Gamsblurb" and new_en.count("Gamsblurb") == 1
    assert new_fr[-1] == "Gamsblurb"


def test_guidepour_does_not_propagate_fiction_across_twins():
    # A real-life-fact guidepour entry: the EN twin has no Fiction, the FR twin (still)
    # does. Fiction must NOT be pulled across onto the EN twin — it stays as authored.
    new_en, new_fr = migrate_tags.plan_pair(
        en_tags=["Djosh Sho", "Guide For", "Gamsblurb"],
        fr_tags=["Fiction", "Djosh Sho", "Guide Pour", "Gamsblurb"])
    assert "Fiction" not in new_en
    assert "Djosh Sho" in new_en and new_en[-1] == "Gamsblurb"
    assert "Fiction" in new_fr           # the side that has it keeps it


def test_non_guidepour_post_still_pairs_fiction():
    # Outside the guidepour column, Fiction pairs across twins like any vocab tag.
    new_en, new_fr = migrate_tags.plan_pair(
        en_tags=["Fiction", "Gamsblurb"], fr_tags=["Gamsblurb"])
    assert "Fiction" in new_en and "Fiction" in new_fr


def test_quote_posts_carry_no_house_tag():
    # A quote (Quote/Citation) is not a Gamsblurb: no house tag is added, and one that a
    # previous (buggy) run wrongly added is stripped on re-run.
    new_en, new_fr = migrate_tags.plan_pair(
        en_tags=["Quote", "Create", "Gamsblurb"],   # the Gamsblurb here = the bad add
        fr_tags=["Citation", "Créer"])
    assert new_en == ["Quote", "Create"]
    assert new_fr == ["Citation", "Créer"]
    assert "Gamsblurb" not in new_en and "Gamsblurb" not in new_fr


def test_duplicate_variants_collapse():
    new_en, _ = migrate_tags.plan_pair(
        en_tags=["Learn", "Learning", "Health"], fr_tags=[])
    assert new_en.count("Learning") == 1       # Learn + Learning -> one concept


# ========================================================================================
# replace_tags_line: surgical, body preserved
_POST = (
    "---\n"
    'title: "Hello"\n'
    "date: 2020-01-01\n"
    "translationKey: 2020-01-01-hello\n"
    "facets: [physics]\n"
    "tags: [Heatlh,Gamsblurb]\n"
    "---\n\n"
    "Body line one.\n\ntags: not a header line.\n"
)


def test_replace_only_touches_the_header_tags_line():
    new_text, changed = migrate_tags.replace_tags_line(_POST, ["Health", "Gamsblurb"])
    assert changed
    assert "tags: [Health,Gamsblurb]" in new_text
    assert "tags: [Heatlh,Gamsblurb]" not in new_text
    # The body's "tags: not a header line." is untouched.
    assert "tags: not a header line." in new_text
    # Everything except the one line is byte-identical.
    assert new_text.replace("tags: [Health,Gamsblurb]", "tags: [Heatlh,Gamsblurb]") == _POST


def test_replace_is_idempotent_when_already_clean():
    clean = _POST.replace("tags: [Heatlh,Gamsblurb]", "tags: [Health,Gamsblurb]")
    new_text, changed = migrate_tags.replace_tags_line(clean, ["Health", "Gamsblurb"])
    assert not changed and new_text == clean


# ========================================================================================
# End-to-end on temp folders
def _write(folder, name, key, facets, tags):
    (folder / name).write_text(
        "---\n"
        'title: "%s"\n' % name +
        "translationKey: %s\n" % key +
        "facets: [%s]\n" % ", ".join(facets) +
        "tags: [%s]\n" % ",".join(tags) +
        "---\n\nBody.\n",
        encoding="utf-8")


def test_migrate_end_to_end(tmp_path):
    en = tmp_path / "en"; en.mkdir()
    fr = tmp_path / "fr"; fr.mkdir()
    _write(en, "2020-01-01-hello.md", "2020-01-01-hello", ["physics"],
           ["Heatlh", "Motivation", "Gamsblurb"])
    _write(fr, "2020-01-01-bonjour.md", "2020-01-01-hello", ["physics"],
           ["santé", "Piano", "Gamsblur"])

    dry = migrate_tags.migrate(str(fr), str(en), write=False, verbose=False)
    assert dry["changed"] == 2 and dry["scanned"] == 2
    # Dry run wrote nothing.
    assert "Heatlh" in (en / "2020-01-01-hello.md").read_text(encoding="utf-8")

    migrate_tags.migrate(str(fr), str(en), write=True, verbose=False)
    en_txt = (en / "2020-01-01-hello.md").read_text(encoding="utf-8")
    fr_txt = (fr / "2020-01-01-bonjour.md").read_text(encoding="utf-8")
    assert "tags: [Health,Motivation,Piano,Gamsblurb]" in en_txt
    assert "tags: [Santé,Piano,Motivation,Gamsblurb]" in fr_txt
    assert "Body." in en_txt and "Body." in fr_txt           # body preserved

    # Idempotent: a second pass changes nothing.
    again = migrate_tags.migrate(str(fr), str(en), write=True, verbose=False)
    assert again["changed"] == 0
