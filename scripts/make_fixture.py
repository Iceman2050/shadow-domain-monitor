#!/usr/bin/env python3
"""Build shadowmon/data/sample-crtsh.json from the generator's own output.

Every fixture domain is asserted to be (or not be) in the lookalike set, so
the demo can never silently drift to zero findings. Re-run after changing
variants.py, then re-embed the README example.

Usage: python3 scripts/make_fixture.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from shadowmon.variants import lookalikes, primary_kind  # noqa: E402

BRAND = "brightacme"
OUT = Path("shadowmon/data/sample-crtsh.json")

LE = "C=US, O=Let's Encrypt, CN=R10"
ZERO = "C=US, O=ZeroSSL, CN=ZeroSSL RSA Domain Secure Site CA"
GTS = "C=US, O=Google Trust Services, CN=WR2"
DIGI = "C=US, O=DigiCert Inc, CN=DigiCert TLS RSA SHA256 2020 CA1"

# (name_value, not_before, issuer, expected_primary_kind or None for ignored)
ROWS = [
    # --- suspicious lookalikes, staggered first-seen dates ---
    ("brightacmeapp.com", "2026-05-20T10:00:00", LE, "affix"),
    ("brightacme.net", "2026-06-05T10:00:00", LE, "tld-swap"),
    ("bright-acme.com", "2026-07-11T10:00:00", ZERO, "hyphenation"),
    ("brigthacme.com", "2026-08-02T10:00:00", LE, "typosquat"),
    ("brightacm3.com", "2026-09-19T10:00:00", GTS, "homoglyph"),
    ("secure-brightacme.com", "2026-10-01T10:00:00", LE, "affix"),
    ("8rightacme.com", "2026-10-09T10:00:00", LE, "homoglyph"),
    ("brightacme.io", "2026-09-02T10:00:00", LE, "tld-swap"),
    # multi-name entry: both names normalize to the same lookalike
    ("secure-brightacme.com\nwww.secure-brightacme.com", "2026-10-03T10:00:00", LE, "affix"),
    # --- known brand domains ---
    ("brightacme.com", "2025-03-14T08:12:00", LE, "exact"),
    ("brightacme.com", "2026-02-01T09:00:00", LE, "exact"),  # later dup: earliest must win
    ("*.brightacme.com", "2026-04-02T10:00:00", DIGI, "exact"),
    # --- noise: real CT-style entries that must NOT match ---
    ("example.com", "2026-01-01T00:00:00", LE, None),
    ("totally-unrelated.org", "2026-02-02T00:00:00", DIGI, None),
]


def main():
    variants = lookalikes(BRAND)
    entries = []
    for i, (name_value, not_before, issuer, expected) in enumerate(ROWS):
        for name in name_value.split():
            norm = name.lower().removeprefix("*.").removeprefix("www.")
            kinds = variants.get(norm)
            if expected is None:
                assert kinds is None, f"noise domain unexpectedly matches: {norm}"
            else:
                assert kinds is not None, f"fixture domain missing from variants: {norm}"
                got = primary_kind(kinds)
                assert got == expected, f"{norm}: kind {got} != {expected}"
        entries.append({
            "issuer_ca_id": 1000 + i,
            "issuer_name": issuer,
            "name_value": name_value,
            "min_cert_id": 9000000 + i,
            "not_before": not_before,
            "not_after": "2027-01-01T00:00:00",
        })
    OUT.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(entries)} entries; "
          f"{sum(1 for r in ROWS if r[3] not in (None, 'exact'))} suspicious rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
