# GenLogin Integration Findings — 2026-11-21

Source plan: `GenLogin_Profile_Manager_Plan.md` v1.0.
Checked (from this VM, 2026-11-21): HackMD "Library Genlogin API"
(https://hackmd.io/@NIYvRudCSk2VsEz_Kps90Q/BJKtmcAka) and
send.win "How to Automate GenLogin API Profiles With Selenium"
(https://blog.send.win/how-to-automate-genlogin-api-profiles-with-selenium/),
which cites the GenLogin Profile API reference at docs.genlogin.com.

## CONFIRMED (public docs, not live-verified on the user's PC)

- GenLogin Local API is a local HTTP service exposed by the GenLogin
  desktop app. Historically: `http://localhost:55550/profiles`,
  Swagger at `http://localhost:55550/api-docs`.
- `getProfiles(limit, offset)` — list profiles. List response is wrapped
  as `{success, data: {lst_profile: [...], pagination: {...}}}`; some
  builds return the arrays at top level. Default page size 20, limit
  capped at 100 in the send.win guide. Field names vary by build
  (`id` / `profile_id`, `name`). **Always print one real profile object
  first and map the keys actually received.**
- `getProfiles(id)` — one profile: `{id, user_id, profile_data, ...}`.
- `getWsEndpoint(id)` — `{success: true, data: {wsEndpoint: '...'}}`.
- `runProfile(id)` — start a profile, returns `wsEndpoint`.
  send.win gives the start path as `GET /profiles/start/{id}`
  (and stop as `GET /profiles/stop/{id}`) but warns paths "have shifted
  between 2.x and 3.0 — confirm the exact path and verb on the reference
  page for your build". The client in this repo therefore tries
  `/profiles/start/{id}` first, then falls back to the older
  `/profiles/run/{id}` spelling, and reports which one answered.
- `stopProfile(id)` — `{success: true}`. Only called when the user
  explicitly asks to stop a profile. This app never auto-closes profiles.
- `getProfilesRunning()` — running profiles.
- Auth is inconsistent across docs: current reference shows
  `Authorization: Bearer <token>` (token from `GENLOGIN_TOKEN` env var);
  2022–2023 wrappers pass an empty key. This app sends the Bearer header
  only when `GENLOGIN_TOKEN` is set, never hardcodes a token, never
  stores one in code, logs or reports.
- API support requires a paid plan (mini-plan and up, per HackMD).
- A script on another machine cannot reach the local API: the caller
  must run on the same Windows PC as GenLogin.

## UPDATE 2026-11-21 — GenLogin 4.5.4 on the user's PC (LIVE, verified by user)

- Root `GET http://localhost:55550/` returns plain text `GenLogin 4.5.4`.
- `GET /profiles` (no trailing slash) -> `404 {"success":false,"status":404,"message":"Endpoint not found"}`
- `GET /api-docs` -> same 404. There is NO Swagger on 4.5.4.
- `GET http://127.0.0.1:8787/profiles` -> `404 {"error":"khong co route"}` — a
  different local service, NOT GenLogin. 8787 is not GenLogin's port.
- Official docs at docs.genlogin.com (checked 2026-11-21, llms.txt +
  genlogin-api/profile-api pages) confirm the CURRENT paths:
  - `GET /profiles/` — list, query offset (default 0), limit (default 20,
    max 100). Response `{success, data: {user_id, lst_profile: [{id,
    user_id, profile_data, name?, group_id?, status, total}], total}}`
  - `POST /profiles/` — create
  - `GET /profiles/{profile_id}/start` — run profile
  - `GET /profiles/{profile_id}/stop` — stop profile
  - `DELETE /profiles/{profile_id}` — delete (never used by this app)
  - Auth: OAuth2PasswordBearer, tokenUrl "/token", header
    `Authorization: Bearer <token>`. Token only from `GENLOGIN_TOKEN`
    env var. Where the token is issued in the GenLogin 4.5.4 app / how
    /token is called is STILL UNCONFIRMED — do not send the user's
    GenLogin password anywhere; ask how they obtain a token, or try
    the list endpoint first without a token (some builds accept it).
- Consequence: the first build used the WRONG paths
  (`/profiles`, `/profiles/start/{id}`, `/profiles/stop/{id}`) from
  secondary guides. Fixed 2026-11-21 to the official paths above,
  with the legacy paths only as fallback after a 404. Mock server
  now 404s `/profiles` (no slash) like real 4.5.4, and serves the
  official paths.
- **TOKEN REQUIRED (docs.genlogin.com, confirmed 2026-11-21):**
  `GET /profiles/` is marked OAuth2PasswordBearer REQUIRED,
  tokenUrl "/token" — i.e. `POST http://localhost:55550/token`.
  Without a token, 4.5.4 returns 404 "Endpoint not found" (it hides
  the endpoint; no 401 is documented). The docs do NOT list the
  /token request fields, and the OpenAPI file backendgenlogin.json
  is 404, so the exact /token body is UNCONFIRMED. The standard
  FastAPI OAuth2 password shape is assumed by
  `scripts/get_token.py`: form `grant_type=password`,
  `username=<GenLogin account email>`, `password=<account password>`.
  That script prompts on the user's PC only, never prints/saves the
  token or password, and only reports the profile count. If /token
  rejects that shape, report its HTTP status/body (redacted) and
  adjust — do NOT send the password anywhere else.
  LIVE UPDATE 2026-11-21 ~10:31: POST /token on the user's PC
  ALSO returns 404 "Endpoint not found" — /token does not exist
  on the local 4.5.4 server at all. It is a cloud-backend endpoint
  in the docs' OpenAPI spec, not a local one. A wrong password
  would give 401/422, never 404, so this is not a password error.
  No public source found says where a local-API token is issued
  (in-app Settings/API, genlogin.com dashboard, or plan-gated —
  old HackMD says "API support from mini-plan"). Next step is
  scripts/probe_api.py: read-only GET probe of ~20 candidate
  paths + netstat for port 55550, to tell 404-everywhere (API off
  / not in this build or plan) apart from 401 (endpoint exists,
  needs a real token) apart from a different live prefix.

## UNKNOWN / NOT VERIFIED — do not assume

- **Port 8787 is NOT confirmed as GenLogin's port.** No public search
  result links 8787 to GenLogin. The user says
  `http://127.0.0.1:8787/` is already running on HIS Windows PC. It may
  be a custom GenLogin port, or a different local service entirely.
  This Muse VM cannot reach the user's PC localhost: `curl` to
  `127.0.0.1:8787` from this VM fails (connection refused) — expected,
  because that is this VM's localhost, not his PC's.
  **Live 8787 was NOT verified from this VM.**
- **Browser-version UPDATE endpoint: UNCONFIRMED / NOT SUPPORTED (yet).**
  No public doc found describes an endpoint that updates only a
  profile's browser version, its request body, field name, or whether
  the profile must be stopped first. The plan (§2, §9) forbids guessing.
  Consequence in this codebase: `VersionService.update_profile()` raises
  `UpdateNotSupportedError`; the Bulk Update UI offers preview + dry-run
  + audit only, and the write button is disabled with an explanation
  until the official method is confirmed from the user's
  `http://127.0.0.1:8787/api-docs` (or `http://localhost:55550/api-docs`).
- Exact start/stop path + verb for the user's installed GenLogin
  version, exact profile field names (`browser_version`? `version`?
  `user_agent`?), group field, and whether update requires stop:
  all UNCONFIRMED until the user runs `scripts/test_connection.py`
  on his PC and opens `/api-docs` there.
- Whether the user's GenLogin plan includes API access: UNCONFIRMED.

## What to do on the user's Windows PC (required before live use)

1. Open `http://127.0.0.1:8787/` and `http://127.0.0.1:8787/api-docs`
   in a browser. Note what answers (GenLogin Swagger? another app?
   nothing?). If nothing answers, try `http://localhost:55550/api-docs`.
2. Run `python scripts/test_connection.py` (read-only GETs only).
3. Try OPEN ONLY on 1–2 test profiles, verify they launch and their
   version/settings are unchanged.
4. Only after step 1–3, paste the `/api-docs` update endpoint (if any)
   back — then the gated update path can be implemented for real.
