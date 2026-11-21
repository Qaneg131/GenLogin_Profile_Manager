"""Read-only GenLogin connection test. Run on the PC where GenLogin runs:
    python scripts/test_connection.py [base_url]
Default base URL: http://127.0.0.1:8787/
Also tries /api-docs. Makes GET requests only — modifies nothing.
Stdlib only, no PySide6 / requests needed.
"""
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.integrations.genlogin_api import GenLoginApi  # noqa: E402


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        "GENLOGIN_BASE_URL", "http://127.0.0.1:8787/")
    print(f"Base URL: {base}")
    api = GenLoginApi(base, timeout=10)
    r = api.test_connection()
    print(json.dumps(r, indent=2, ensure_ascii=False))
    if not r.get("ok"):
        print("\nFAILED. Is GenLogin running on THIS PC? "
              "Try http://localhost:55550/ as base URL.")
        return 1
    try:
        profiles, pagination = api.list_profiles(0, 5)
        print(f"\nFirst page: {len(profiles)} profile(s); pagination={pagination}")
        for p in profiles:
            print(f"  - {p.id} | {p.name} | version={p.browser_version} | running={p.running}")
            print(f"    raw keys: {sorted(p.raw.keys())}")
    except Exception as e:  # noqa: BLE001
        print(f"\nList failed: {e}")
        return 1
    try:
        with urllib.request.urlopen(base.rstrip("/") + "/api-docs", timeout=5) as resp:
            print(f"\n/api-docs: HTTP {resp.status} (Swagger available — check it for the update endpoint)")
    except Exception as e:  # noqa: BLE001
        print(f"\n/api-docs: not reachable ({e})")
    print("\nOK — read-only test passed. No profiles were launched or modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
