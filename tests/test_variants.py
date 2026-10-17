"""Variant-generation tests (pure logic, no network)."""

import pytest

from shadowmon.variants import TLDs, lookalikes, primary_kind


@pytest.fixture(scope="module")
def variants():
    return lookalikes("brightacme")


def test_exact_brand_on_canonical_tld(variants):
    assert variants["brightacme.com"] == {"exact"}


def test_known_typosquat_present(variants):
    assert "brigthacme.com" in variants  # transposition
    assert "typosquat" in variants["brigthacme.com"]


def test_known_homoglyphs_present(variants):
    assert "brightacm3.com" in variants  # e -> 3
    assert "8rightacme.com" in variants  # b -> 8
    assert "homoglyph" in variants["brightacm3.com"]


def test_known_hyphenation_present(variants):
    assert "bright-acme.com" in variants
    assert "hyphenation" in variants["bright-acme.com"]


def test_known_affixes_present(variants):
    assert "secure-brightacme.com" in variants
    assert "brightacme-login.com" in variants
    assert "affix" in variants["secure-brightacme.com"]


def test_tld_swap_coverage(variants):
    for tld in ("net", "io", "xyz", "ai"):
        assert f"brightacme.{tld}" in variants, f"missing TLD {tld}"
    assert "tld-swap" in variants["brightacme.net"]


def test_all_domains_lowercase_and_unique():
    v = lookalikes("BrightAcme")
    assert all(d == d.lower() for d in v)
    assert "brightacme.com" in v  # brand normalized


def test_empty_brand_rejected():
    with pytest.raises(ValueError):
        lookalikes("  ")


def test_variant_count_sane(variants):
    # typosquat combinatorics should yield thousands of domains
    assert len(variants) > 1000, f"only {len(variants)} variants"


def test_primary_kind_prefers_suspicious_over_exact():
    assert primary_kind({"exact", "tld-swap"}) == "tld-swap"
    assert primary_kind({"exact"}) == "exact"
    assert primary_kind({"typosquat", "affix"}) == "typosquat"


def test_unrelated_domain_absent(variants):
    assert "example.com" not in variants
    assert "totally-unrelated.org" not in variants
