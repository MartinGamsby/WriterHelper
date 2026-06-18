import popularity


# ========================================================================================
# Worklist enumeration: only readable post links survive the filter
# ========================================================================================
def _post(title, key, footer):
    return ("---\n"
            "title: %s\n"
            "date: 2024-03-02\n"
            "translationKey: %s\n"
            "facets: [dev]\n"
            "tags: [Gamsblurb]\n"
            "---\n\n"
            "Body paragraph.\n\n"
            "---\n\n%s" % (title, key, footer))


def _write(folder, name, text):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(text, encoding="utf-8")


def test_is_url():
    assert popularity._is_url("https://x.com/a") and popularity._is_url("http://a")
    assert not popularity._is_url("Just some post text")
    assert not popularity._is_url("  ftp://nope ")


def test_worklist_keeps_engagement_urls_drops_reference_and_nonurl(tmp_path):
    en = tmp_path / "en"
    _write(en, "2024-03-02-a.md", _post("Post A", "2024-03-02-post-a",
        "- [X/Twitter](https://x.com/me/status/123)\n"
        "- [YouTube](https://youtu.be/xyz)\n"
        "- [Source](https://example.com/origin)\n"))          # reference slot: skipped
    _write(en, "2024-03-02-b.md", _post("Post B", "2024-03-02-post-b",
        "- [Bluesky](Legacy post text\nspanning two lines)\n"))  # non-URL legacy: skipped

    rows = popularity.collect_worklist("", str(en))
    platforms = {(r["platform"], r["hl"]) for r in rows}
    assert platforms == {("X/Twitter", "en"), ("YouTube", "en")}
    x = next(r for r in rows if r["platform"] == "X/Twitter")
    assert x["url"] == "https://x.com/me/status/123"
    assert x["key"] == "2024-03-02-post-a" and x["title"] == "Post A"


def test_worklist_spans_both_languages(tmp_path):
    fr, en = tmp_path / "fr", tmp_path / "en"
    _write(fr, "2024-03-02-a.md", _post("Billet", "k1",
        "- [Bluesky](https://bsky.app/profile/me.bsky.social/post/abc)\n"))
    _write(en, "2024-03-02-a.md", _post("Post", "k1",
        "- [X/Twitter](https://x.com/me/status/9)\n"))
    rows = popularity.collect_worklist(str(fr), str(en))
    assert {(r["platform"], r["hl"]) for r in rows} == {
        ("Bluesky", "fr"), ("X/Twitter", "en")}


def test_worklist_handles_missing_folder():
    assert popularity.collect_worklist("/no/such/fr", "/no/such/en") == []


def test_worklist_filters_by_platform_and_hl(tmp_path):
    fr, en = tmp_path / "fr", tmp_path / "en"
    _write(fr, "2024-03-02-a.md", _post("Billet", "k1",
        "- [Bluesky](https://bsky.app/profile/me.bsky.social/post/abc)\n"
        "- [X/Twitter](https://x.com/me/status/1)\n"))
    _write(en, "2024-03-02-a.md", _post("Post", "k1",
        "- [X/Twitter](https://x.com/me/status/9)\n"))
    only_x = popularity.collect_worklist(str(fr), str(en), platforms=["X/Twitter"])
    assert {r["platform"] for r in only_x} == {"X/Twitter"} and len(only_x) == 2
    en_x = popularity.collect_worklist(str(fr), str(en), platforms=["X/Twitter"], hls=["en"])
    assert len(en_x) == 1 and en_x[0]["hl"] == "en"


# ========================================================================================
# Ledger: append-only, same-day merge, sorted snapshots
# ========================================================================================
def _reading(key, platform, metrics, hl="en"):
    return {"key": key, "hl": hl, "platform": platform,
            "url": "https://x/%s" % key, "metrics": metrics}


def test_record_snapshot_merges_same_day_by_id():
    ledger = {"snapshots": []}
    popularity.record_snapshot(ledger, "2026-05-01", [
        _reading("a", "X/Twitter", {"likes": 10}),
        _reading("b", "Bluesky", {"likes": 5})])
    # Re-run same day with an updated reading for "a": overwrite, don't duplicate.
    popularity.record_snapshot(ledger, "2026-05-01", [
        _reading("a", "X/Twitter", {"likes": 12})])
    assert len(ledger["snapshots"]) == 1
    readings = ledger["snapshots"][0]["readings"]
    assert len(readings) == 2
    a = next(r for r in readings if r["key"] == "a")
    assert a["metrics"]["likes"] == 12


def test_record_snapshot_keeps_snapshots_date_sorted():
    ledger = {"snapshots": []}
    popularity.record_snapshot(ledger, "2026-05-01", [_reading("a", "X/Twitter", {"likes": 1})])
    popularity.record_snapshot(ledger, "2026-04-01", [_reading("a", "X/Twitter", {"likes": 1})])
    assert [s["date"] for s in ledger["snapshots"]] == ["2026-04-01", "2026-05-01"]


def test_ledger_round_trips_through_disk(tmp_path):
    path = str(tmp_path / "popularity.json")
    ledger = popularity.load_ledger(path)            # missing file -> empty
    assert ledger == {"snapshots": []}
    popularity.record_snapshot(ledger, "2026-05-01", [_reading("a", "X/Twitter", {"likes": 7})])
    popularity.save_ledger(ledger, path)
    assert popularity.load_ledger(path)["snapshots"][0]["readings"][0]["metrics"]["likes"] == 7


# ========================================================================================
# Summary: primary metric, sum fallback, deltas vs the previous snapshot
# ========================================================================================
def test_primary_value_uses_platform_metric_then_sum_fallback():
    assert popularity.primary_value(_reading("a", "X/Twitter", {"likes": 9, "reposts": 2})) == 9
    # Medium's primary is "claps"; absent -> sum of the numeric metrics present.
    assert popularity.primary_value(_reading("a", "Medium", {"responses": 3, "views": 100})) == 103
    assert popularity.primary_value(_reading("a", "Medium", {})) == 0


def test_summarize_ranks_and_computes_deltas():
    ledger = {"snapshots": []}
    popularity.record_snapshot(ledger, "2026-04-01", [_reading("a", "X/Twitter", {"likes": 8})])
    popularity.record_snapshot(ledger, "2026-05-01", [
        _reading("a", "X/Twitter", {"likes": 12}),                 # +4 vs April
        _reading("b", "Medium", {"responses": 3, "views": 100})])  # new, fallback 103
    summary = popularity.summarize(ledger)
    assert summary["date"] == "2026-05-01" and summary["prev_date"] == "2026-04-01"
    # Ranked by value desc: Medium fallback (103) outranks X (12).
    assert [r["key"] for r in summary["rows"]] == ["b", "a"]
    by_key = {r["key"]: r for r in summary["rows"]}
    assert by_key["a"]["delta"] == 4
    assert by_key["b"]["delta"] is None        # first time seen


def test_summarize_empty_ledger():
    assert popularity.summarize({"snapshots": []})["rows"] == []


def test_format_summary_smoke():
    ledger = {"snapshots": []}
    popularity.record_snapshot(ledger, "2026-05-01", [_reading("a", "X/Twitter", {"likes": 7})])
    out = popularity.format_summary(popularity.summarize(ledger))
    assert "2026-05-01" in out and "X/Twitter" in out
    assert popularity.format_summary({"date": None, "prev_date": None, "rows": []}) \
        == "No readings recorded yet."
