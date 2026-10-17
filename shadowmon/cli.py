"""CLI for shadow-domain-monitor."""

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .ct import CTError, fetch_certs, load_fixture, parse_entries
from .match import find_matches
from .report import render_markdown
from .variants import lookalikes
from .webhook import build_payload, post_webhook

DATA_DIR = Path(__file__).resolve().parent / "data"
SAMPLE = DATA_DIR / "sample-crtsh.json"

DEMO_BRAND = "brightacme"


def build_parser():
    p = argparse.ArgumentParser(
        prog="shadowmon",
        description="Watch Certificate Transparency logs for lookalike domains of your brand.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("--brand", help="Brand keyword, e.g. 'acme' (required unless --demo)")
    p.add_argument("--live", action="store_true",
                   help="Query crt.sh over the network (default: use the bundled cached sample)")
    p.add_argument("--demo", action="store_true",
                   help="30-second demo against the cached sample response")
    p.add_argument("--fixture", default=None,
                   help="Path to a cached crt.sh JSON response (default: bundled sample)")
    p.add_argument("--webhook-url", default=None,
                   help="POST the alert payload JSON to this URL (any JSON receiver)")
    p.add_argument("--print-payload", action="store_true",
                   help="Print the webhook payload JSON after the report")
    p.add_argument("--out", default=None, help="Write the markdown report to a file")
    p.add_argument("--generated-at", default=None,
                   help="Override the generated timestamp (default: now, UTC)")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.demo:
        brand, live, fixture_path = DEMO_BRAND, False, None
    else:
        if not args.brand:
            parser.error("--brand is required (or use --demo)")
        brand, live, fixture_path = args.brand, args.live, args.fixture

    variants = lookalikes(brand)

    if live:
        try:
            entries = fetch_certs(brand)
        except CTError as e:
            raise SystemExit(f"error: {e}")
    else:
        path = Path(fixture_path) if fixture_path else SAMPLE
        try:
            entries = load_fixture(path)
        except (OSError, json.JSONDecodeError) as e:
            raise SystemExit(f"error: cannot load fixture {path}: {e}")

    records = parse_entries(entries)
    suspicious, known = find_matches(records, variants)
    report = render_markdown(brand, suspicious, known, len(records),
                             generated_at=args.generated_at)

    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"Wrote {args.out} ({len(suspicious)} suspicious lookalikes)")
    else:
        sys.stdout.write(report)

    payload = build_payload(brand, suspicious, generated_at=args.generated_at)
    if args.webhook_url:
        try:
            status, body = post_webhook(args.webhook_url, payload)
        except OSError as e:
            raise SystemExit(f"error: webhook POST failed: {e}")
        print(f"Webhook POST -> {args.webhook_url}: HTTP {status}")
        if body.strip():
            print(body.strip()[:500])
    if args.print_payload or args.webhook_url:
        if not args.webhook_url:
            print()
            print("--- webhook payload (not sent; pass --webhook-url to send) ---")
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
