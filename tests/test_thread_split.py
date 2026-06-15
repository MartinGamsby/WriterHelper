import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import thread_split  # noqa: E402


# ========================================================================================
def test_short_text_is_one_segment():
    assert thread_split.split_text("Hello world.", 280) == ["Hello world."]


def test_every_segment_within_limit():
    text = "\n\n".join("Paragraph number %d has some words in it." % n for n in range(40))
    segs = thread_split.split_text(text, 100, number=False)
    assert len(segs) > 1
    assert all(len(s) <= 100 for s in segs)


def test_numbered_segments_still_fit_the_limit():
    text = ("sentence. " * 200).strip()
    segs = thread_split.number_segments(thread_split.split_text(text, 80, number=True))
    assert len(segs) > 1
    assert all(len(s) <= 80 for s in segs)         # counter accounted for in the budget
    assert segs[0].endswith("(1/%d)" % len(segs))


def test_prefers_paragraph_boundaries():
    text = "First paragraph here.\n\nSecond paragraph here.\n\nThird paragraph here."
    segs = thread_split.split_text(text, 25, number=False)
    # Each short paragraph stands alone rather than being cut mid-paragraph.
    assert segs == ["First paragraph here.", "Second paragraph here.", "Third paragraph here."]


def test_falls_back_to_sentences_then_words():
    text = "Alpha beta gamma delta epsilon zeta eta theta iota kappa lambda."
    segs = thread_split.split_text(text, 20, number=False)
    assert len(segs) > 1
    assert all(len(s) <= 20 for s in segs)
    assert segs[0].startswith("Alpha")


def test_hard_wraps_an_unbreakable_token():
    segs = thread_split.split_text("x" * 50, 20, number=False)
    assert segs == ["x" * 20, "x" * 20, "x" * 10]


def test_number_segments_leaves_single_alone():
    assert thread_split.number_segments(["only one"]) == ["only one"]


def test_join_and_split_round_trip():
    segs = ["one", "two", "three"]
    blob = thread_split.join_for_edit(segs)
    assert thread_split.SEPARATOR in blob
    assert thread_split.split_on_separator(blob) == segs


def test_split_on_separator_tolerates_extra_dashes_and_whitespace():
    blob = "one\n-----\n  two  \n---\n\n\nthree"
    assert thread_split.split_on_separator(blob) == ["one", "two", "three"]


def test_split_on_separator_drops_empty_segments():
    assert thread_split.split_on_separator("   \n---\n   ") == []
