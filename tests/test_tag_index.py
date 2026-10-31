import tag_index


def _post(folder, name, facets, tags):
    (folder / name).write_text(
        "---\n"
        "title: \"%s\"\n" % name +
        "facets: [%s]\n" % ", ".join(facets) +
        "tags: [%s]\n" % ",".join(tags) +
        "---\n\nbody\n",
        encoding="utf-8")


def _corpus(tmp_path):
    folder = tmp_path / "en"
    folder.mkdir()
    _post(folder, "a.md", ["dev"], ["Programming", "Code", "Gamsblurb"])
    _post(folder, "b.md", ["dev"], ["Programming", "Learn", "Gamsblurb"])   # Learn->Learning
    _post(folder, "c.md", ["physics"], ["Gravity", "Science", "Gamsblurb"])
    _post(folder, "d.md", ["dev", "ideas"], ["Programming", "Productivity", "Gamsblurb"])
    return str(folder)


def test_popular_ranks_by_frequency_and_drops_house_tag(tmp_path):
    folder = _corpus(tmp_path)
    pop = tag_index.popular(folder, "en")
    assert pop[0] == "Programming"          # used on 3 posts
    assert "Gamsblurb" not in pop           # house tag is on every post -> not suggested


def test_synonyms_fold_to_one_concept(tmp_path):
    folder = _corpus(tmp_path)
    pop = tag_index.popular(folder, "en")
    assert "Learning" in pop and "Learn" not in pop   # "Learn" counted as "Learning"


def test_matching_uses_facet_cooccurrence(tmp_path):
    folder = _corpus(tmp_path)
    # An article tagged dev should be offered the tags that co-occur with dev posts,
    # NOT the physics-only ones.
    match = tag_index.matching(folder, "en", ["dev"])
    assert match[0] == "Programming"
    assert "Gravity" not in match and "Science" not in match
    assert set(["Code", "Learning", "Productivity"]).issubset(set(match))


def test_matching_empty_without_facets(tmp_path):
    folder = _corpus(tmp_path)
    assert tag_index.matching(folder, "en", []) == []


def test_exclude_already_applied(tmp_path):
    folder = _corpus(tmp_path)
    match = tag_index.matching(folder, "en", ["dev"], exclude=["Programming"])
    assert "Programming" not in match


def test_cache_invalidates_when_folder_changes(tmp_path):
    import pathlib
    folder = _corpus(tmp_path)
    before = tag_index.popular(folder, "en")
    assert "Habits" not in before
    _post(pathlib.Path(folder), "e.md", ["dev"], ["Habits", "Gamsblurb"])  # a brand-new tag
    after = tag_index.popular(folder, "en")
    assert "Habits" in after        # the rebuilt index sees the new post


def test_fr_labels_returned_for_fr_folder(tmp_path):
    folder = tmp_path / "fr"
    folder.mkdir()
    _post(folder, "a.md", ["dev"], ["Apprentissage", "Programmation", "Gamsblurb"])
    _post(folder, "b.md", ["dev"], ["Learn", "Gamsblurb"])     # leak -> folds to Apprentissage(fr)
    pop = tag_index.popular(str(folder), "fr")
    assert "Apprentissage" in pop          # both posts, including the EN-leak "Learn"
    assert "Learn" not in pop and "Learning" not in pop
