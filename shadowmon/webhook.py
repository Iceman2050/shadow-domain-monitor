"""Vendor-neutral alerting: build a generic JSON webhook payload, optionally POST it.

No vendor lock-in: any HTTPS endpoint that accepts JSON works
(Slack incoming webhooks, PagerDuty Events API, n8n, a tiny Flask receiver...).
"""

import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen


def build_payload(brand, suspicious, generated_at=None):
    """Build the alert payload dict."""
    generated_at = generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "event": "shadow_domain_watch",
        "brand": brand,
        "generated_at": generated_at,
        "suspicious_count": len(suspicious),
        "findings": [
            {
                "domain": f["domain"],
                "kind": f["kind"],
                "first_seen": f["first_seen"],
                "issuer": f["issuer"],
                "cert_count": f["cert_count"],
            }
            for f in suspicious
        ],
    }


def post_webhook(url, payload, timeout=10):
    """POST the payload as JSON. Returns (status_code, response_body)."""
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data,
                  headers={"Content-Type": "application/json",
                           "User-Agent": "shadow-domain-monitor/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read().decode("utf-8", errors="replace")
