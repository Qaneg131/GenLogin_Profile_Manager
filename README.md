# GenLogin Profile Manager

Windows desktop app (Python + PySide6) to manage GenLogin profiles in bulk.
Plan: `GenLogin_Profile_Manager_Plan.md` v1.0. Integration findings:
`docs/INTEGRATION_FINDINGS.md` — read it first.

## Modes
- **OPEN ONLY** — launch selected profiles, never changes version/settings. Fully implemented.
- **UPDATE ONLY** — preview + Dry Run only. **Write path is GATED/disabled**: no documented
  browser-version update endpoint was found in public GenLogin docs. Do not guess one.
- **UPDATE + OPEN** — same gate: launches only verified-success updates (none until the gate lifts).

## Safety rules (plan §2)
Never delete / clone / reset profiles. Never change proxy, cookies, fingerprint,
user-agent or other settings except the one change the user explicitly requests.
Never silently close a running profile to update it. Success is verified by
re-reading state, never assumed from a sent request. No secrets in code, logs
or reports. Token (if any) comes only from the `GENLOGIN_TOKEN` env var.

## Setup (Windows, on the PC where GenLogin runs)
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
GenLogin must be running on **this same PC** — the Local API is localhost-only.
Default base URL: `http://127.0.0.1:8787/` (`config/settings.json`).
Classic GenLogin default is `http://localhost:55550/` — change it in Settings
if `8787` is not GenLogin on your PC.

## Run
```bat
python -m app.main
```

## Connection test (read-only, before any launch)
```bat
python scripts/test_connection.py
python scripts/test_connection.py http://localhost:55550/
```
Also open in a browser on that PC: `http://127.0.0.1:8787/` and
`http://127.0.0.1:8787/api-docs` — paste what you see back if the update
endpoint is listed there.

## Tests (mock only — NOT live GenLogin)
```bat
python -m py_compile app/main.py app/ui/*.py app/core/*.py app/integrations/*.py app/services/*.py app/storage/*.py scripts/test_connection.py tests/*.py
python -m unittest tests.test_api_client -v
```
The mock server (`tests/test_mock_server.py`) serves 3 sample profiles on
`127.0.0.1:8787` in the test VM only.

## Test plan (on Windows, live)
1. Connection test above → profile count matches GenLogin.
2. Profile Manager → Refresh, search "shop", filter running.
3. OPEN ONLY on 1–2 test profiles → verify they launch, version unchanged.
4. Already-running profile → skipped, reported.
5. Bulk Update → Preview + Dry Run change nothing; Execute stays disabled.
6. Pause / Resume / Stop during a bulk open; restart app → interrupted
   tasks are flagged, not auto-resumed.

## Layout
```
app/main.py  app/ui/ (8 pages)  app/core/  app/integrations/genlogin_api.py
app/services/  app/storage/ (SQLite data/app.db)  config/settings.json
logs/ screenshots/<task_id>/<profile_id>_<ts>.png  exports/  docs/  scripts/  tests/
```

## Packaging (later, Phase 5)
```bat
pip install pyinstaller
pyinstaller --noconfirm --windowed --name GenLoginProfileManager app/main.py
```
