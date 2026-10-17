"""Matching + report tests (fixture-driven, no network)."""

from pathlib import Path

from shadowmon.ct import load_fixture, parse_entries
from shadowmon.match import find_matches
from shadowmon.report import render_markdown
from shadowmon.variants import lookalikes

DATA = Path(__file__).resolve().parent.parent / "shadowmon" / "data" / "sample-crtsh.json"


def run_fixture():
    variants = lookalikes("brightacme")
    records = parse_entries(load_fixture(DATA))
    return find_matches(records, variants), records


def test_fixture_finds_expected_suspicious():
    (suspicious, known), _ = run_fixture()
    domains = {f["domain"] for f in suspicious}
    for d in ("brightacmeapp.com", "brightacme.net", "bright-acme.com",
              "brigthacme.com", "brightacm3.com", "secure-brightacme.com",
              "8rightacme.com", "brightacme.io"):
        assert d in domains, f"missing suspicious {d}"


def test_noise_domains_ignored():
    (suspicious, known), _ = run_fixture()
    domains = {f["domain"] for f in suspicious} | {f["domain"] for f in known}
    assert "example.com" not in domains
    assert "totally-unrelated.org" not in domains


def test_known_brand_separated():
    (suspicious, known), _ = run_fixture()
    assert {f["domain"] for f in known} == {"brightacme.com"}
    assert all(f["kind"] != "exact" for f in suspicious)


def test_earliest_first_seen_wins():
    (suspicious, known), _ = run_fixture()
    rec = next(f for f in known if f["domain"] == "brightacme.com")
    assert rec["first_seen"] == "2025-03-14T08:12:00"


def test_suspicious_sorted_oldest_first():
    (suspicious, _), _ = run_fixture()
    assert suspicious[0]["domain"] == "brightacmeapp.com"
    assert suspicious[-1]["domain"] == "8rightacme.com"


def test_cert_count_aggregates_multi_name_entry():
    (suspicious, _), _ = run_fixture()
    rec = next(f for f in suspicious if f["domain"] == "secure-brightacme.com")
    assert rec["cert_count"] == 3


def test_report_contains_rows_oldest_first():
    (suspicious, known), records = run_fixture()
    md = render_markdown("brightacme", suspicious, known, len(records),
                         generated_at="2026-10-17T00:00:00+00:00")
    assert md.startswith("# Shadow-domain watch report — brightacme")
    assert "| brightacmeapp.com | affix |" in md
    assert md.index("brightacmeapp.com") < md.index("8rightacme.com")
    assert "Generated 2026-10-17T00:00:00+00:00" in md


def test_report_empty_findings():
    md = render_markdown("zzz-no-match", [], [], 3, generated_at="2026-10-17T00:00:00+00:00")
    assert "Suspicious lookalikes (0)" in md
    assert "No lookalike domains found" in md


def test_report_deterministic():
    (suspicious, known), records = run_fixture()
    a = render_markdown("brightacme", suspicious, known, len(records),
                        generated_at="2026-10-17T00:00:00+00:00")
    b = render_markdown("brightacme", suspicious, known, len(records),
                        generated_at="2026-10-17T00:00:00+00:00")
    assert a == b
