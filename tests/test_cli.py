"""CLI tests (offline: fixture mode only)."""

import pytest

from shadowmon.cli import main


def test_demo_prints_report(capsys):
    assert main(["--demo", "--generated-at", "2026-10-17T00:00:00+00:00"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("# Shadow-domain watch report — brightacme")
    assert "brigthacme.com" in out
    assert "Generated 2026-10-17T00:00:00+00:00" in out


def test_brand_required_without_demo():
    with pytest.raises(SystemExit):
        main([])


def test_brand_uses_bundled_fixture(capsys):
    # any brand works offline against the bundled sample
    assert main(["--brand", "brightacme", "--generated-at", "2026-10-17T00:00:00+00:00"]) == 0
    out = capsys.readouterr().out
    assert "Shadow-domain watch report" in out


def test_out_writes_file(tmp_path):
    dest = tmp_path / "report.md"
    assert main(["--demo", "--out", str(dest),
                 "--generated-at", "2026-10-17T00:00:00+00:00"]) == 0
    assert "Shadow-domain watch report" in dest.read_text(encoding="utf-8")


def test_print_payload(capsys):
    assert main(["--demo", "--print-payload",
                 "--generated-at", "2026-10-17T00:00:00+00:00"]) == 0
    out = capsys.readouterr().out
    assert '"event": "shadow_domain_watch"' in out
    assert '"suspicious_count": 8' in out


def test_missing_fixture_errors(tmp_path):
    with pytest.raises(SystemExit):
        main(["--brand", "brightacme",
              "--fixture", str(tmp_path / "nope.json")])
