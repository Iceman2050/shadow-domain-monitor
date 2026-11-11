# shadow-domain-monitor

**Attackers register lookalike domains of your brand — and nobody notices for months.**

Every certificate issued for a lookalike domain is published in public
Certificate Transparency logs. This tool turns your brand keyword into
thousands of lookalike variants (typosquats, homoglyphs, hyphenations,
security-lure affixes, TLD swaps), queries CT logs for them, and produces a
watch report ordered by **registration timing** — oldest first, because the
longer a lookalike has held a certificate, the more urgent the review.
Alerting is a plain JSON webhook payload: point it at any receiver, no vendor
lock-in.

## Quickstart

```bash
# 30-second demo: cached sample CT response, full watch report
python -m shadowmon --demo

# Watch your own brand against the LIVE CT log (network)
python -m shadowmon --brand acme --live

# Save the report and print the alert payload
python -m shadowmon --brand acme --live --out watch-report.md --print-payload

# Send the alert payload to any JSON webhook (Slack, PagerDuty, n8n, ...)
python -m shadowmon --brand acme --live \
  --webhook-url https://your-receiver.example.com/hook
```

No dependencies beyond Python 3.9+ stdlib. The demo and the test suite run
fully offline against a bundled cached CT response; only `--live` touches the
network (crt.sh JSON API).

## Example output

Fresh from `python -m shadowmon --demo --generated-at 2026-10-17T00:00:00+00:00`
(byte-for-byte verified — see "Verification" below):

<!-- EXAMPLE-OUTPUT-START -->
```markdown
# Shadow-domain watch report — brightacme

Generated 2026-10-17T00:00:00+00:00 · 15 certificates scanned · 8 suspicious lookalikes

## Suspicious lookalikes (8)

Oldest first — the longer a lookalike has held a certificate, the more urgent the review.

| Domain | Type | First seen (cert) | Issuer | Certs |
|---|---|---|---|---|
| brightacmeapp.com | affix | 2026-05-20T10:00:00 | C=US, O=Let's Encrypt, CN=R10 | 1 |
| brightacme.net | tld-swap | 2026-06-05T10:00:00 | C=US, O=Let's Encrypt, CN=R10 | 1 |
| bright-acme.com | hyphenation | 2026-07-11T10:00:00 | C=US, O=ZeroSSL, CN=ZeroSSL RSA Domain Secure Site CA | 1 |
| brigthacme.com | typosquat | 2026-08-02T10:00:00 | C=US, O=Let's Encrypt, CN=R10 | 1 |
| brightacme.io | tld-swap | 2026-09-02T10:00:00 | C=US, O=Let's Encrypt, CN=R10 | 1 |
| brightacm3.com | homoglyph | 2026-09-19T10:00:00 | C=US, O=Google Trust Services, CN=WR2 | 1 |
| secure-brightacme.com | affix | 2026-10-01T10:00:00 | C=US, O=Let's Encrypt, CN=R10 | 3 |
| 8rightacme.com | homoglyph | 2026-10-09T10:00:00 | C=US, O=Let's Encrypt, CN=R10 | 1 |

## Known brand domains observed (1)

- brightacme.com (first seen 2025-03-14T08:12:00)

---
_Watches Certificate Transparency logs only — see "What it does NOT do" in the README._
```
<!-- EXAMPLE-OUTPUT-END -->

## How it works

1. **Variant generation** (`shadowmon/variants.py`): from your brand keyword it
   builds lookalikes — single/double typos, transpositions, homoglyph swaps
   (`o→0`, `e→3`, `l→1`…), hyphen insertions, lure affixes (`secure-`,
   `-login`, `-support`, `-pay`…), and the brand on 16 TLDs.
2. **CT query** (`shadowmon/ct.py`): hits the crt.sh JSON API
   (`https://crt.sh/?q=%.{brand}%&output=json`), or reads a cached response.
3. **Matching** (`shadowmon/match.py`): normalizes observed names (wildcards,
   `www.` stripped), matches against the variant set, keeps the earliest
   certificate date per domain as first-seen.
4. **Report + alert** (`shadowmon/report.py`, `shadowmon/webhook.py`):
   markdown report oldest-first, plus a generic JSON payload you can POST
   anywhere.

## Verification

- `python -m pytest tests/ -q` — 37 tests, all green. Tests use fixtures and
  local throwaway HTTP servers only; `grep -rn "https://" tests/` is empty —
  no test touches the real network.
- The example above is regenerated from a fresh tool run and diffed against
  this README by `scripts/embed_example.py --check`.
- The bundled fixture (`shadowmon/data/sample-crtsh.json`) is built by
  `scripts/make_fixture.py` **from the generator's own variant set** — every
  fixture lookalike is asserted present, every noise domain asserted absent —
  so the demo can't silently drift to zero findings.

## What it does NOT do

- **It watches Certificate Transparency logs, not DNS registrations.** A
  lookalike domain with no certificate is invisible to this tool. Pair it with
  a DNS-monitoring feed for full coverage.
- It does not take anything down: no registrar API, no abuse-report filing —
  it produces the watch report and the alert payload; takedown is your call.
- Variant generation is heuristic. Attackers invent spellings no generator
  predicts; treat "0 findings" as "0 found", not "all clear".
- `--live` depends on crt.sh availability and rate limits; cache responses for
  repeated runs.

## Built by Ingenious AI
- DisclosureGuard — https://wa.me/5016691053?text=Hi%20Ingenious%20AI%21%20I%20want%20early%20access%20to%20DisclosureGuard.
- ModelMinder — https://wa.me/5016691053?text=Hi%20Ingenious%20AI%21%20I%20want%20early%20access%20to%20ModelMinder.
- TermsWatch — https://wa.me/5016691053?text=Hi%20Ingenious%20AI%21%20I%20want%20early%20access%20to%20TermsWatch.
- Vibe-Code Audit — https://wa.me/5016691053?text=Hi%20Ingenious%20AI%21%20I%20want%20early%20access%20to%20Vibe-Code%20Audit.
- Rogue-Agent Defense — https://wa.me/5016691053?text=Hi%20Ingenious%20AI%21%20I%20want%20early%20access%20to%20Rogue-Agent%20Defense.
- BreachHunter — https://wa.me/5016691053?text=Hi%20Ingenious%20AI%21%20I%20want%20early%20access%20to%20BreachHunter.
- ChatBreaker — https://wa.me/5016691053?text=Hi%20Ingenious%20AI%21%20I%20want%20early%20access%20to%20ChatBreaker.
- Agent Flight Recorder — https://wa.me/5016691053?text=Hi%20Ingenious%20AI%21%20I%20want%20early%20access%20to%20Agent%20Flight%20Recorder.
- Agent Auth Gateway — https://wa.me/5016691053?text=Hi%20Ingenious%20AI%21%20I%20want%20early%20access%20to%20Agent%20Auth%20Gateway.
- DomainGuard — https://wa.me/5016691053?text=Hi%20Ingenious%20AI%21%20I%20want%20early%20access%20to%20DomainGuard.
- ContentCraft AI — https://wa.me/5016691053?text=Hi%20Ingenious%20AI%21%20I%20want%20early%20access%20to%20ContentCraft%20AI.

## License

MIT — see [LICENSE](LICENSE).
