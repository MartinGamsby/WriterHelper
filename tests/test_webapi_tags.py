import tag_vocab
from webapi import Api


def _seed_post(model, hl, title, facets, tags):
    a = model.get(hl)
    a.set_title(title)
    a.set_content("body " * 30)
    a.set_facets(facets)
    a.set_tags(tags)


def test_toggle_tag_adds_then_removes_and_pairs(pair):
    api = Api(pair)
    pair.en().set_title("Hello")
    pair.fr().set_title("Bonjour")

    api.toggle_tag("en", "Health")
    assert "Health" in tag_vocab.split(pair.en().tags)
    assert "Santé" in tag_vocab.split(pair.fr().tags)        # paired onto the twin

    # Toggling any label of the same concept removes it from both sides.
    api.toggle_tag("en", "Health")
    assert "Health" not in tag_vocab.split(pair.en().tags)
    assert "Santé" not in tag_vocab.split(pair.fr().tags)


def test_tag_suggestions_matching_and_popular_are_disjoint(pair):
    # Build a tiny corpus in the EN posts folder via the model.
    _seed_post(pair, "en", "P1", ["dev"], "Programming,Code,Gamsblurb")
    pair.en().new_article()
    _seed_post(pair, "en", "P2", ["dev"], "Programming,Gamsblurb")
    pair.en().new_article()
    _seed_post(pair, "en", "P3", ["physics"], "Gravity,Gamsblurb")
    pair.en().new_article()

    # The article currently being edited is tagged dev.
    _seed_post(pair, "en", "Draft", ["dev"], "Gamsblurb")

    api = Api(pair)
    out = api.tag_suggestions("en")
    assert "Programming" in out["matching"]          # co-occurs with dev
    assert "Gravity" not in out["matching"]           # physics-only
    # The two lists never overlap (matching wins).
    assert set(out["matching"]).isdisjoint(set(out["popular"]))
    # The house tag is never suggested.
    assert "Gamsblurb" not in out["matching"] + out["popular"]
