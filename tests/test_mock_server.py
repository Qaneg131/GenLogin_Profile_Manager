"""Mock GenLogin server for local verification ONLY.
Serves a sample /profiles payload on 127.0.0.1:8787 in this VM.
This is NOT live GenLogin — see docs/INTEGRATION_FINDINGS.md.
Run: python -m tests.test_mock_server  (then Ctrl+C)
Or use tests/test_api_client.py which starts it automatically.
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PROFILES = [
    {"id": "prof-001", "name": "Shop 1", "group": "Shop",
     "browser_type": "Chrome", "browser_version": "155", "is_running": False},
    {"id": "prof-002", "name": "Shop 2", "group": "Shop",
     "browser_type": "Chrome", "browser_version": "156", "is_running": True},
    {"id": "prof-003", "name": "Ads 1", "group": "Ads",
     "browser_type": "Chrome", "browser_version": "154", "is_running": False},
]
RUNNING = {"prof-002"}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body))); self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        from urllib.parse import urlparse, parse_qs
        u = urlparse(self.path)
        if u.path == "/token":
            length = int(self.headers.get("Content-Length") or 0)
            fields = parse_qs(self.rfile.read(length).decode())
            if fields.get("username") and fields.get("password"):
                return self._json({"access_token": "mock-token-123",
                                   "token_type": "bearer"})
            return self._json({"detail": "missing credentials"}, 422)
        return self._json({"success": False, "message": "unknown path"}, 404)

    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        u = urlparse(self.path)
        # Official 4.5.4 list path is /profiles/ WITH trailing slash;
        # /profiles without it 404s on real GenLogin 4.5.4, so mock it too.
        if u.path == "/profiles":
            return self._json({"success": False, "status": 404,
                               "message": "Endpoint not found"}, 404)
        if u.path == "/profiles/":
            q = parse_qs(u.query)
            off = int(q.get("offset", ["0"])[0]); lim = int(q.get("limit", ["100"])[0])
            page = []
            for x in PROFILES[off:off + lim]:
                y = dict(x); y["is_running"] = x["id"] in RUNNING; page.append(y)
            return self._json({"success": True, "data": {
                "user_id": 1, "total": len(PROFILES),
                "lst_profile": page,
                "pagination": {"total": len(PROFILES), "offset": off, "limit": lim}}})
        if u.path.endswith("/start"):
            pid = u.path.split("/")[2]
            RUNNING.add(pid)
            return self._json({"success": True, "data": {
                "wsEndpoint": f"ws://127.0.0.1:53412/devtools/browser/{pid}"}})
        if u.path.endswith("/stop"):
            RUNNING.discard(u.path.split("/")[2])
            return self._json({"success": True})
        if u.path.startswith("/profiles/"):
            pid = u.path.rstrip("/").rsplit("/", 1)[-1]
            p = next((x for x in PROFILES if x["id"] == pid), None)
            if p:
                p = dict(p); p["is_running"] = pid in RUNNING
                return self._json({"success": True, "data": p})
            return self._json({"success": False, "message": "not found"}, 404)
        if u.path == "/api-docs":
            return self._json({"success": False, "status": 404,
                               "message": "Endpoint not found"}, 404)
        return self._json({"success": False, "message": "unknown path"}, 404)


if __name__ == "__main__":
    print("Mock GenLogin on http://127.0.0.1:8787/ (MOCK ONLY, not live GenLogin)")
    ThreadingHTTPServer(("127.0.0.1", 8787), Handler).serve_forever()
