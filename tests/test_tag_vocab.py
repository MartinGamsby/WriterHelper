import tag_vocab


# ========================================================================================
def test_casefold_and_accents_casing_collapse():
    # Pure casing / accent-casing variants resolve without an explicit alias.
    for raw in ("Personal Development", "Personal development", "personal development"):
        assert tag_vocab.concept_id(raw) == "Personal Development"
    for raw in ("Développement Personnel", "Développement personnel",
                "développement personnel"):
        assert tag_vocab.canonical_label(raw, "en") == "Personal Development"


def test_typos_and_merged_words_resolve():
    assert tag_vocab.canonical_label("Heatlh", "en") == "Health"
    assert tag_vocab.canonical_label("Allimentation", "fr") == "Alimentation"
    for broken in ("Gamsblur", "GamsblogGamsblurb", "GamsBlurb", "gamsblurb"):
        assert tag_vocab.canonical_label(broken, "en") == "Gamsblurb"


def test_synonyms_merge_to_one_concept():
    # EN Learn/Learning and FR Apprendre/Apprentissage are the same concept.
    assert tag_vocab.concept_id("Learn") == "Learning"
    assert tag_vocab.concept_id("Apprendre") == "Learning"
    assert tag_vocab.canonical_label("Learn", "fr") == "Apprentissage"
    assert tag_vocab.canonical_label("Apprendre", "en") == "Learning"


def test_cross_language_leak_reflows_to_file_language():
    # A French physics tag sitting in an EN file becomes its English label.
    assert tag_vocab.canonical_label("Astrophysique", "en") == "Astrophysics"
    assert tag_vocab.canonical_label("Trou Noir", "en") == "Black Hole"
    # An English tag in a FR file becomes its French label.
    assert tag_vocab.canonical_label("Purpose", "fr") == "Raison d'Être"


def test_unknown_tag_passes_through_trimmed():
    assert tag_vocab.normalize("Some Obscure One-Off") is None
    assert tag_vocab.canonical_label("  Some Obscure One-Off  ", "en") == "Some Obscure One-Off"
    assert tag_vocab.canonical_label("Some Obscure One-Off", "fr") == "Some Obscure One-Off"


def test_concepts_in_dedupes_and_orders():
    # "Learn" and "Learning" are the same concept -> counted once, in first-seen order.
    s = "Health,Learn,Gamsblurb,Learning,Totally Custom"
    assert tag_vocab.concepts_in(s) == ["Health", "Learning", "Gamsblurb"]


def test_split_join_roundtrip():
    assert tag_vocab.split(" Health , Learning ,, Gamsblurb ") == \
        ["Health", "Learning", "Gamsblurb"]
    assert tag_vocab.join(["Health", "Learning"]) == "Health,Learning"


def test_no_concept_silently_shadowed_by_alias_collision():
    # Every concept's own EN and FR label must resolve back to itself: a key claimed
    # by an earlier concept would shadow a later one and corrupt the migration.
    for c in tag_vocab.CONCEPTS:
        assert tag_vocab.concept_id(c["en"]) == c["id"], c
        assert tag_vocab.concept_id(c["fr"]) == c["id"], c


def test_house_tag_present():
    assert tag_vocab.HOUSE_TAG == "Gamsblurb"
    assert tag_vocab.concept_id("Gamsblurb") == "Gamsblurb"
