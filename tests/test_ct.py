"""CT querying/parsing tests. Network only via a local throwaway HTTP server."""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from shadowmon.ct import CTError, fetch_certs, load_fixture, normalize_domain, parse_entries, parse_not_before
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "shadowmon" / "data" / "sample-crtsh.json"


class _Handler(BaseHTTPRequestHandler):
    body = b"[]"

    def do_GET(self):
        data = _Handler.body
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture()
def local_ct():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def test_fetch_against_local_server(local_ct):
    _Handler.body = json.dumps([
        {"issuer_name": "C=US, O=Test CA", "name_value": "ex ample.com",
         "not_before": "2026-01-01T00:00:00"},
    ]).encode()
    entries = fetch_certs("ample", base_url=local_ct)
    assert len(entries) == 1
    assert entries[0]["name_value"] == "ex ample.com"


def test_fetch_connection_refused_raises_cterror():
    with pytest.raises(CTError):
        fetch_certs("x", base_url="http://127.0.0.1:1", timeout=2)


def test_fetch_bad_json_raises_cterror(local_ct):
    _Handler.body = b"not json at all"
    with pytest.raises(CTError):
        fetch_certs("x", base_url=local_ct)


def test_fetch_non_list_json_raises_cterror(local_ct):
    _Handler.body = b'{"error": "nope"}'
    with pytest.raises(CTError):
        fetch_certs("x", base_url=local_ct)


def test_load_fixture():
    entries = load_fixture(DATA)
    assert isinstance(entries, list) and len(entries) >= 10


def test_parse_entries_splits_and_normalizes():
    recs = parse_entries([
        {"name_value": "*.Example.COM\nwww.example.com", "not_before": "2026-01-01T00:00:00",
         "issuer_name": "C=US, O=CA"},
    ])
    domains = [r["domain"] for r in recs]
    assert domains == ["example.com", "example.com"]


def test_normalize_domain():
    assert normalize_domain("*.Foo.COM") == "foo.com"
    assert normalize_domain("www.foo.com") == "foo.com"
    assert normalize_domain("  FOO.com ") == "foo.com"


def test_parse_not_before():
    assert parse_not_before("2026-09-19T10:00:00") is not None
    assert parse_not_before("") is None
    assert parse_not_before("garbage") is None
