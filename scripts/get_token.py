"""Get a GenLogin Bearer token, then test GET /profiles/ with it.

Why this exists: official docs (docs.genlogin.com, Profile API) mark
GET /profiles/ as OAuth2PasswordBearer REQUIRED, tokenUrl "/token".
On the user's PC, GET /profiles/ with NO token returns 404, but
with a (dummy) Bearer token it returns 500 "Invalid token
specified" — so the endpoint EXISTS and is gated by token auth.

Key correction (2026-11-21): /token does NOT exist on the LOCAL
server (POST http://localhost:55550/token -> 404). The tokenUrl in
the docs belongs to GenLogin's CLOUD backend, whose OpenAPI spec
lives at https://backend.genlogin.com/openapi.json — so this script
POSTs the credentials to https://backend.genlogin.com/token FIRST
(standard OAuth2 password flow), and only falls back to the local
/token afterwards. The returned token is then used against the
LOCAL server http://localhost:55550/profiles/.

How it works (credentials stay on YOUR PC; the password is never
printed or written to disk, and the token is never printed):
  1. Prompts for your GenLogin account email + password (hidden).
  2. POSTs them as form data (grant_type=password, username=...,
     password=...) to the token URL(s) above.
  3. If a token comes back, calls GET /profiles/ on the local
     server with "Authorization: Bearer <token>" and prints only
     the profile count + first profile names.
  4. Tells you the PowerShell command to set GENLOGIN_TOKEN for
     the current session, so the app / test_connection.py can use
     it. The token is NOT saved to any file by this script.

Run on the PC where GenLogin runs:
    python scripts/get_token.py [base_url]
    python scripts/get_token.py http://localhost:55550/
"""
import getpass
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.integrations.genlogin_api import GenLoginApi  # noqa: E402
from app.core.models import redact  # noqa: E402


def post_token(url, username, password):
    body = urllib.parse.urlencode({
        "grant_type": "password",
        "username": username,
        "password": password,
    }).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")[:500]
        print(f"{url} returned HTTP {e.code}: {redact(raw)}")
        return None
    except Exception as e:  # noqa: BLE001
        print(f"Could not reach {url}: {e}")
        return None


def get_token(username, password, local_base):
    """Try the cloud backend first, then the local server."""
    for url in ("https://backend.genlogin.com/token",
                local_base.rstrip("/") + "/token"):
        print(f"Trying {url} ...")
        data = post_token(url, username, password)
        if data:
            token = data.get("access_token") or data.get("token")
            if token:
                print(f"Token received from {url} (not shown).")
                return token
            print(f"{url} answered but gave no access_token field.")
            print(f"Response keys: {sorted(data.keys())}")
    return None


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        "GENLOGIN_BASE_URL", "http://localhost:55550/")
    print(f"Base URL: {base}")
    print("This will ask for your GenLogin account email/password.")
    print("They are sent ONLY to GenLogin's own token endpoint")
    print("(https://backend.genlogin.com/token, then localhost as fallback).")
    username = input("GenLogin email / username: ").strip()
    password = getpass.getpass("GenLogin password (hidden): ")
    if not username or not password:
        print("Cancelled — no username/password entered.")
        return 1
    token = get_token(username, password, base)
    if not token:
        print("\nNo token received. Do NOT paste your password anywhere —")
        print("tell me the HTTP status above and I will adjust the request.")
        return 1
    print("\nTesting GET /profiles/ on the local server with it...")
    os.environ["GENLOGIN_TOKEN"] = token
    api = GenLoginApi(base, timeout=10)
    r = api.test_connection()
    print(json.dumps(r, indent=2, ensure_ascii=False))
    if not r.get("ok"):
        print("\nToken did not unlock /profiles/. Tell me the error above.")
        return 1
    profiles, _ = api.list_profiles(0, 5)
    print(f"\nOK — {len(profiles)} profile(s) on first page:")
    for p in profiles:
        print(f"  - {p.id} | {p.name} | version={p.browser_version}")
    print("\nTo use the token in this PowerShell session (paste the token")
    print("value yourself — this script does not print it):")
    print('  $env:GENLOGIN_TOKEN="<paste token here>"')
    print("Then run:")
    print("  python scripts\\test_connection.py http://localhost:55550/")
    print("  python -m app.main")
    print("Note: the token lives only in that PowerShell window;")
    print("close the window and it is gone. Do not save it in a file,")
    print("and do not paste it into chat.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
