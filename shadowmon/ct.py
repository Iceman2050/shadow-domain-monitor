"""Certificate-transparency querying (crt.sh JSON API) and parsing.

Network use is isolated here. Everything else works on parsed records,
so tests and the demo run fully offline against fixtures.
"""

import json
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

CRT_SH = "https://crt.sh"


class CTError(Exception):
    """The CT log could not be queried or its response parsed."""


def fetch_certs(brand, timeout=20, base_url=CRT_SH):
    """Query crt.sh for certificates matching %.<brand>%. Returns raw entries.

    base_url is injectable so tests can point at a local HTTP server.
    """
    url = f"{base_url}/?q=%25.{quote(brand)}%25&output=json"
    req = Request(url, headers={"User-Agent": "shadow-domain-monitor/1.0"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except (URLError, HTTPError, TimeoutError, OSError) as e:
        raise CTError(f"could not query CT log at {base_url}: {e}") from e
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError as e:
        raise CTError(f"CT log returned unparsable JSON: {e}") from e
    if not isinstance(entries, list):
        raise CTError("CT log returned unexpected JSON shape")
    return entries


def normalize_domain(name):
    """Lowercase, strip wildcard and www prefixes."""
    d = name.strip().lower()
    if d.startswith("*."):
        d = d[2:]
    if d.startswith("www."):
        d = d[4:]
    return d


def parse_entries(entries):
    """Flatten crt.sh entries into records.

    Returns list of dicts: {domain, not_before (raw str), issuer}.
    name_value may hold several whitespace-separated names.
    """
    records = []
    for e in entries:
        names = str(e.get("name_value", "")).split()
        issuer = str(e.get("issuer_name", ""))
        not_before = str(e.get("not_before", ""))
        for n in names:
            domain = normalize_domain(n)
            if domain:
                records.append({
                    "domain": domain,
                    "not_before": not_before,
                    "issuer": issuer,
                })
    return records


def parse_not_before(value):
    """Parse a crt.sh not_before timestamp; None if unparseable."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def load_fixture(path):
    """Load a cached crt.sh-style JSON response from disk."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)
