"""Render the watch report as markdown."""

from datetime import datetime, timezone


def render_markdown(brand, suspicious, known, total_certs, generated_at=None):
    """Build the markdown watch report."""
    generated_at = generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    lines = [
        f"# Shadow-domain watch report — {brand}",
        "",
        f"Generated {generated_at} · {total_certs} certificates scanned · "
        f"{len(suspicious)} suspicious lookalike{'s' if len(suspicious) != 1 else ''}",
        "",
    ]
    if suspicious:
        lines.append(f"## Suspicious lookalikes ({len(suspicious)})")
        lines.append("")
        lines.append("Oldest first — the longer a lookalike has held a certificate, "
                     "the more urgent the review.")
        lines.append("")
        lines.append("| Domain | Type | First seen (cert) | Issuer | Certs |")
        lines.append("|---|---|---|---|---|")
        for f in suspicious:
            lines.append(f"| {f['domain']} | {f['kind']} | {f['first_seen']} "
                         f"| {f['issuer']} | {f['cert_count']} |")
        lines.append("")
    else:
        lines.append("## Suspicious lookalikes (0)")
        lines.append("")
        lines.append("No lookalike domains found in Certificate Transparency logs.")
        lines.append("")
    if known:
        lines.append(f"## Known brand domains observed ({len(known)})")
        lines.append("")
        for f in known:
            lines.append(f"- {f['domain']} (first seen {f['first_seen']})")
        lines.append("")
    lines.append("---")
    lines.append("_Watches Certificate Transparency logs only — see "
                 "\"What it does NOT do\" in the README._")
    return "\n".join(lines).rstrip() + "\n"
