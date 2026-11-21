"""Get a GenLogin Bearer token LOCALLY, then test GET /profiles/ with it.

Why this exists: official docs (docs.genlogin.com, Profile API) mark
GET /profiles/ as OAuth2PasswordBearer REQUIRED, tokenUrl "/token".
Without a token, GenLogin 4.5.4 returns 404 "Endpoint not found" —
it hides the endpoint instead of returning 401.

How it works (all on YOUR PC, nothing is sent to anyone else):
  1. Prompts for your GenLogin account email + password (password is
     hidden with getpass, never printed, never written to disk).
  2. POSTs them as form data to http://localhost:55550/token
     (standard FastAPI OAuth2 password flow:
     grant_type=password, username=..., password=...).
     If that shape is wrong for your build, it prints the server's
     status/body (with any token redacted) so we can adjust — it does
     NOT guess further or retry with other credentials.
  3. If a token comes back, it calls GET /profiles/ with
     "Authorization: Bearer <token>" and prints only the profile
     count + first profile names. It NEVER prints the token itself.
  4. It tells you the exact PowerShell command to set GENLOGIN_TOKEN
     for the current session, so the app / test_connection.py can use
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


def post_token(base, username, password):
    url = base.rstrip("/") + "/token"
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
        print(f"/token returned HTTP {e.code}: {redact(raw)}")
        return None
    except Exception as e:  # noqa: BLE001
        print(f"Could not reach {url}: {e}")
        return None


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        "GENLOGIN_BASE_URL", "http://localhost:55550/")
    print(f"Base URL: {base}")
    print("This will ask for your GenLogin account email/password.")
    print("They are used ONLY for this one POST to localhost, on this PC.")
    username = input("GenLogin email / username: ").strip()
    password = getpass.getpass("GenLogin password (hidden): ")
    if not username or not password:
        print("Cancelled — no username/password entered.")
        return 1
    data = post_token(base, username, password)
    if not data:
        print("\nNo token received. Do NOT paste your password anywhere —")
        print("tell me the HTTP status above and I will adjust the request.")
        return 1
    token = data.get("access_token") or data.get("token")
    if not token:
        print("\n/token answered but gave no access_token field.")
        print(f"Response keys: {sorted(data.keys())}")
        return 1
    print("\nToken received (not shown). Testing GET /profiles/ with it...")
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
