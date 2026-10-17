"""Generate lookalike domain variants for a brand keyword.

Kinds:
  exact        - the brand itself on the canonical TLD
  typosquat    - insertion / deletion / substitution / transposition / doubling
  homoglyph    - single lookalike-character swaps (0/O, 1/l, 3/e, ...)
  hyphenation  - hyphens inserted inside the brand
  affix        - security-lure prefixes/suffixes (secure-, -login, -support, ...)
  tld-swap     - the exact brand label on a non-canonical TLD
"""

import string

TLDs = (
    "com", "net", "org", "io", "co", "ai", "app", "dev",
    "xyz", "info", "biz", "online", "site", "shop", "us", "me",
)

CANONICAL_TLD = "com"

HOMOGLYPHS = {
    "a": ("4",),
    "b": ("8",),
    "e": ("3",),
    "g": ("9",),
    "i": ("1",),
    "l": ("1",),
    "o": ("0",),
    "s": ("5",),
    "t": ("7",),
}

AFFIXES = (
    "get", "my", "the", "secure", "login", "support", "pay", "help",
    "app", "hq", "team", "portal", "verify", "account",
)

LETTERS = string.ascii_lowercase


def _typosquats(label):
    out = set()
    n = len(label)
    for i in range(n):
        out.add(label[:i] + label[i + 1:])            # deletion
        out.add(label[:i] + label[i] + label[i:])     # doubling
        if i < n - 1:
            out.add(label[:i] + label[i + 1] + label[i] + label[i + 2:])  # transpose
        for c in LETTERS:
            out.add(label[:i] + c + label[i:])        # insertion
            if c != label[i]:
                out.add(label[:i] + c + label[i + 1:])  # substitution
    for c in LETTERS:
        out.add(label + c)                            # insertion at end
    out.discard(label)
    return {w for w in out if w}


def _homoglyphs(label):
    out = set()
    for i, ch in enumerate(label):
        for rep in HOMOGLYPHS.get(ch, ()):
            out.add(label[:i] + rep + label[i + 1:])
    return out


def _hyphenations(label):
    return {label[:i] + "-" + label[i:] for i in range(1, len(label))}


def _affixes(label):
    out = set()
    for a in AFFIXES:
        out.add(a + label)
        out.add(label + a)
        out.add(a + "-" + label)
        out.add(label + "-" + a)
    out.add(label + "s")  # plural
    return out


def lookalikes(brand, tlds=TLDs, canonical_tld=CANONICAL_TLD):
    """Return {domain: set(kinds)} of lookalike domains for brand.

    brand: keyword like "brightacme" (case-insensitive).
    """
    label = brand.strip().lower()
    if not label:
        raise ValueError("brand must not be empty")

    label_kinds = {label: {"exact"}}
    for w in _typosquats(label):
        label_kinds.setdefault(w, set()).add("typosquat")
    for w in _homoglyphs(label):
        label_kinds.setdefault(w, set()).add("homoglyph")
    for w in _hyphenations(label):
        label_kinds.setdefault(w, set()).add("hyphenation")
    for w in _affixes(label):
        label_kinds.setdefault(w, set()).add("affix")

    domains = {}
    for w, kinds in label_kinds.items():
        for tld in tlds:
            domain = f"{w}.{tld}"
            if w == label and tld == canonical_tld:
                domains[domain] = {"exact"}
            else:
                dk = set(kinds)
                if w == label:
                    dk.add("tld-swap")
                domains.setdefault(domain, set()).update(dk)
    return domains


KIND_PRIORITY = ("typosquat", "homoglyph", "hyphenation", "affix", "tld-swap", "exact")


def primary_kind(kinds):
    """Pick the most report-worthy kind from a set.

    Suspicious kinds outrank "exact": the bare brand on a non-canonical TLD
    (kinds {"exact", "tld-swap"}) is a lookalike worth flagging, while the
    brand on the canonical TLD (just {"exact"}) is a known domain.
    """
    for k in KIND_PRIORITY:
        if k in kinds:
            return k
    return sorted(kinds)[0]
