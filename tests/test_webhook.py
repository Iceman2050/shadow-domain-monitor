"""Webhook payload + POST tests. POST goes to a local throwaway HTTP server."""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from shadowmon.webhook import build_payload, post_webhook

FINDINGS = [
    {"domain": "brigthacme.com", "kind": "typosquat",
     "first_seen": "2026-08-02T10:00:00", "issuer": "C=US, O=CA", "cert_count": 1},
]


class _Handler(BaseHTTPRequestHandler):
    received = None

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        _Handler.received = self.rfile.read(length)
        body = b'{"ok": true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture()
def local_receiver():
    _Handler.received = None
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}/hook"
    server.shutdown()


def test_build_payload_structure():
    p = build_payload("brightacme", FINDINGS, generated_at="2026-10-17T00:00:00+00:00")
    assert p["event"] == "shadow_domain_watch"
    assert p["brand"] == "brightacme"
    assert p["generated_at"] == "2026-10-17T00:00:00+00:00"
    assert p["suspicious_count"] == 1
    assert p["findings"][0]["domain"] == "brigthacme.com"
    assert set(p["findings"][0]) == {"domain", "kind", "first_seen", "issuer", "cert_count"}
    json.dumps(p)  # must be JSON-serializable


def test_post_webhook_delivers_json(local_receiver):
    payload = build_payload("brightacme", FINDINGS, generated_at="2026-10-17T00:00:00+00:00")
    status, body = post_webhook(local_receiver, payload)
    assert status == 200
    assert json.loads(body) == {"ok": True}
    got = json.loads(_Handler.received.decode("utf-8"))
    assert got["event"] == "shadow_domain_watch"
    assert got["findings"][0]["domain"] == "brigthacme.com"


def test_post_webhook_failure_raises(local_receiver):
    with pytest.raises(OSError):
        post_webhook("http://127.0.0.1:1/hook",
                     build_payload("x", [], generated_at="2026-10-17T00:00:00+00:00"),
                     timeout=2)
