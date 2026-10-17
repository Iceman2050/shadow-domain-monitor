#!/usr/bin/env python3
"""Regenerate the README's Example output block from a FRESH tool run.

The block between <!-- EXAMPLE-OUTPUT-START --> and <!-- EXAMPLE-OUTPUT-END -->
is replaced with a fenced copy of `python -m shadowmon --demo` output.
A fixed --generated-at keeps the output deterministic so the README stays
byte-for-byte verifiable.

Usage: python3 scripts/embed_example.py [--check]
  --check: exit 1 if the README block differs from a fresh run (no rewrite).
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
START = "<!-- EXAMPLE-OUTPUT-START -->"
END = "<!-- EXAMPLE-OUTPUT-END -->"
DEMO_AT = "2026-10-17T00:00:00+00:00"


def fresh_output():
    r = subprocess.run(
        [sys.executable, "-m", "shadowmon", "--demo", "--generated-at", DEMO_AT],
        capture_output=True, text=True, cwd=ROOT, timeout=60,
    )
    if r.returncode != 0:
        raise SystemExit(f"demo run failed: {r.stderr}")
    return r.stdout


def fenced(output):
    return "```markdown\n" + output.rstrip("\n") + "\n```\n"


def extract_block(text):
    try:
        i = text.index(START) + len(START)
        j = text.index(END)
    except ValueError:
        return None
    return text[i:j]


def main():
    fresh_block = "\n" + fenced(fresh_output())
    text = README.read_text(encoding="utf-8")
    current = extract_block(text)
    if current is None:
        raise SystemExit("markers not found in README")
    if "--check" in sys.argv:
        if current != fresh_block:
            print("MISMATCH: README example differs from fresh tool run")
            return 1
        print("OK: README example matches fresh tool run byte-for-byte")
        return 0
    new_text = (text[: text.index(START) + len(START)] + fresh_block
                + text[text.index(END):])
    README.write_text(new_text, encoding="utf-8")
    print(f"Embedded fresh demo output into {README}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
