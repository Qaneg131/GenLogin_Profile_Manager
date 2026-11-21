"""Probe GenLogin 4.5.4's local server — READ ONLY, no credentials.

Background: on the user's PC, GET /profiles/ AND POST /token both
return 404 "Endpoint not found" on http://localhost:55550/, and
GET /api-docs also 404s. The docs' /token endpoint therefore does
NOT exist on the local server — it belongs to GenLogin's cloud API.
No public source says where a local-API token is issued, so before
guessing more endpoints we map what actually exists on port 55550.

This script only does GET requests and prints status + a short
snippet of each response. It never sends a password or token, and
the one dummy Bearer header ("Bearer probe-dummy-token") is fake —
it is only there to tell 404 (endpoint absent) apart from 401
(endpoint exists, needs a real token).

It also runs `netstat -ano` and prints the lines for port 55550,
so we can see which process owns the port, and tries `tasklist`
for a GenLogin process (Windows only; both steps are best-effort).

Run on the PC where GenLogin runs:
    python scripts/probe_api.py [base_url]
    python scripts/probe_api.py http://localhost:55550/
"""
import os
import subprocess
import sys
import urllib.error
import urllib.request

PATHS = [
    "/",
    "/profiles",
    "/profiles/",
    "/api/profiles",
    "/api/profiles/",
    "/api/v1/profiles",
    "/v1/profiles",
    "/profiles/list",
    "/profiles/running",
    "/api-docs",
    "/docs",
    "/openapi.json",
    "/api/openapi.json",
    "/swagger",
    "/token",
    "/status",
    "/health",
    "/version",
    "/api/version",
    "/api/status",
]


def get(base, path, headers=None):
    url = base.rstrip("/") + path
    req = urllib.request.Request(url, method="GET")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            body = r.read(200).decode("utf-8", "replace")
            return r.status, body
    except urllib.error.HTTPError as e:
        body = e.read(200).decode("utf-8", "replace")
        return e.code, body
    except Exception as e:  # noqa: BLE001
        return None, str(e)


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        "GENLOGIN_BASE_URL", "http://localhost:55550/")
    print(f"Base URL: {base}\n")
    print("== Listening port ==")
    try:
        out = subprocess.run(["netstat", "-ano"], capture_output=True,
                             text=True, timeout=15).stdout
        lines = [l for l in out.splitlines() if "55550" in l]
        print("\n".join(lines) if lines else
              "No line for 55550 in netstat — is GenLogin running?")
    except Exception as e:  # noqa: BLE001
        print(f"netstat not available: {e}")
    print("\n== GenLogin process ==")
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq GenLogin*"],
                             capture_output=True, text=True,
                             timeout=15).stdout
        print(out.strip()[:800])
    except Exception as e:  # noqa: BLE001
        print(f"tasklist not available: {e}")

    print("\n== Candidate paths (GET, no auth) ==")
    for p in PATHS:
        code, body = get(base, p)
        snippet = " ".join(body.split())[:110] if body else ""
        print(f"{str(code):>5}  {p:<22} {snippet}")

    print("\n== GET /profiles/ with a DUMMY Bearer header ==")
    code, body = get(base, "/profiles/",
                     {"Authorization": "Bearer probe-dummy-token"})
    print(f"{code}  {body[:200]}")
    print("\nHow to read this:")
    print("- 404 on EVERYTHING except / : the local API is off / not")
    print("  in this build — check the GenLogin app: your plan, and")
    print("  any Settings > API / Local API switch. Old docs say API")
    print("  support starts at the Mini plan.")
    print("- 401 on /profiles/ with the dummy token: the endpoint")
    print("  EXISTS and needs a real token — tell me, and we will")
    print("  find where GenLogin issues it (app or genlogin.com).")
    print("- 200 on some other path: that is the real API prefix —")
    print("  tell me which path, and I will rewire the app to it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
