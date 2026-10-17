"""Match observed certificate domains against lookalike variants."""

from .ct import parse_not_before
from .variants import primary_kind


def find_matches(records, variants):
    """Split parsed cert records into suspicious lookalikes vs known domains.

    Returns (suspicious, known): lists of dicts
      {domain, kind, first_seen (raw str), issuer, cert_count},
    suspicious sorted oldest-first (registration timing = triage priority).
    """
    by_domain = {}
    for r in records:
        kinds = variants.get(r["domain"])
        if not kinds:
            continue
        slot = by_domain.setdefault(r["domain"], {
            "domain": r["domain"],
            "kinds": set(),
            "first_seen": r["not_before"],
            "issuer": r["issuer"],
            "cert_count": 0,
        })
        slot["kinds"].update(kinds)
        slot["cert_count"] += 1
        cur = parse_not_before(slot["first_seen"])
        new = parse_not_before(r["not_before"])
        if new and (cur is None or new < cur):
            slot["first_seen"] = r["not_before"]
            slot["issuer"] = r["issuer"]

    suspicious, known = [], []
    for slot in by_domain.values():
        kind = primary_kind(slot["kinds"])
        item = {
            "domain": slot["domain"],
            "kind": kind,
            "first_seen": slot["first_seen"],
            "issuer": slot["issuer"],
            "cert_count": slot["cert_count"],
        }
        (known if kind == "exact" else suspicious).append(item)

    suspicious.sort(key=lambda f: (parse_not_before(f["first_seen"]) or f["first_seen"]))
    known.sort(key=lambda f: f["domain"])
    return suspicious, known
