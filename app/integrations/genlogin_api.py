"""GenLogin Local API adapter — stdlib only (urllib), no extra deps.

Confirmed from OFFICIAL docs (docs.genlogin.com, checked 2026-11-21,
GenLogin 4.5.4 on the user's PC — root GET / returns "GenLogin 4.5.4"):
  GET {base}/profiles/            list (offset default 0, limit default 20,
                                  max 100) — NOTE trailing slash.
                                  Returns {success, data: {user_id,
                                  lst_profile: [{id, user_id, profile_data,
                                  name?, group_id?, status, total}],
                                  total}}
  GET {base}/profiles/{id}/start  start a profile (runProfile)
  GET {base}/profiles/{id}/stop   stop (explicit user request only)
  POST {base}/profiles/           create (NOT used by this app)
  DELETE {base}/profiles/{id}     delete (NOT used by this app — never
                                  delete profiles)
  Auth: OAuth2PasswordBearer, tokenUrl "/token" — send
  "Authorization: Bearer <token>". Token comes only from the
  GENLOGIN_TOKEN env var, never hardcoded/stored in code.
  There is NO /api-docs on 4.5.4 (GET /api-docs -> 404 "Endpoint not
  found"), and GET /profiles (no trailing slash) -> 404 on 4.5.4.
  Legacy fallbacks (/profiles/start/{id}, /profiles/stop/{id}) are
  tried only after the official path 404s, for older builds.

NOT implemented: any browser-version update call — no documented
endpoint exists (see VersionService). Do not guess one here.
"""
from __future__ import annotations
import json
import os
import urllib.error
import urllib.request
from typing import Optional

from app.core.models import Profile, redact


class GenLoginApiError(Exception):
    pass


class GenLoginApi:
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.token = os.environ.get("GENLOGIN_TOKEN", "")  # never hardcoded

    # -- low level -----------------------------------------------------
    def _request(self, method: str, path: str, params: dict | None = None):
        from urllib.parse import urlencode
        url = self.base_url + path
        if params:
            url += "?" + urlencode(params)
        req = urllib.request.Request(url, method=method)
        req.add_header("Content-Type", "application/json")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                body = r.read().decode("utf-8", "replace")
                return json.loads(body) if body.strip() else {}
        except urllib.error.HTTPError as e:
            raise GenLoginApiError(
                f"HTTP {e.code} on {method} {path}: "
                f"{redact(e.read().decode('utf-8', 'replace')[:500])}") from e
        except urllib.error.URLError as e:
            raise GenLoginApiError(
                f"Cannot reach GenLogin at {self.base_url} "
                f"({redact(str(e.reason))}). Is GenLogin running on this PC?") from e

    @staticmethod
    def _unwrap(payload) -> dict:
        if isinstance(payload, dict) and "data" in payload:
            return payload["data"] if isinstance(payload["data"], dict) else payload
        return payload if isinstance(payload, dict) else {}

    # -- read-only -----------------------------------------------------
    def test_connection(self) -> dict:
        """Read-only probe: GET /profiles/?limit=1. Returns status info."""
        try:
            payload = self._request("GET", "/profiles/", {"limit": 1, "offset": 0})
            data = self._unwrap(payload)
            total = (data.get("pagination") or {}).get("total")
            if total is None:
                total = data.get("total")
            return {"ok": True, "base_url": self.base_url,
                    "total": total, "raw_keys": sorted(data.keys())[:20]}
        except GenLoginApiError as e:
            return {"ok": False, "base_url": self.base_url, "error": str(e)}

    def list_profiles(self, offset: int = 0, limit: int = 100) -> tuple[list[Profile], dict]:
        payload = self._request("GET", "/profiles/", {"offset": offset, "limit": limit})
        data = self._unwrap(payload)
        raw = data.get("lst_profile") or data.get("profiles") or []
        if isinstance(payload, list):
            raw = payload
        return [Profile.from_api(p) for p in raw if isinstance(p, dict)], \
            data.get("pagination") or {}

    def list_all_profiles(self, page_size: int = 100) -> list[Profile]:
        out, offset = [], 0
        while True:
            batch, _ = self.list_profiles(offset, page_size)
            out.extend(batch)
            if len(batch) < page_size:
                break
            offset += page_size
        return out

    def get_profile(self, profile_id: str) -> Optional[Profile]:
        for path in (f"/profiles/{profile_id}/", f"/profiles/{profile_id}"):
            try:
                payload = self._request("GET", path)
            except GenLoginApiError as e:
                if "HTTP 404" in str(e):
                    continue
                raise
            data = self._unwrap(payload)
            return Profile.from_api(data) if data else None
        return None

    def list_running(self) -> list[Profile]:
        # No running-list endpoint in the official 4.5.4 docs; the list
        # response carries a status/is_running field per profile.
        # Fallback: running flag on the full list (slower, documented
        # fields only).
        return [p for p in self.list_all_profiles() if p.running]

    def is_running(self, profile_id: str) -> bool:
        return any(p.id == profile_id for p in self.list_running())

    # -- launch (OPEN ONLY: read/launch only, never edits settings) ----
    def run_profile(self, profile_id: str) -> dict:
        """Start a profile. Official path first
        (GET /profiles/{id}/start), legacy path only as fallback.
        Returns the raw payload incl. wsEndpoint when present."""
        last_err = None
        for path in (f"/profiles/{profile_id}/start",
                     f"/profiles/start/{profile_id}",
                     f"/profiles/run/{profile_id}"):
            try:
                return self._request("GET", path)
            except GenLoginApiError as e:
                last_err = e
                if "HTTP 404" not in str(e):
                    raise
        raise last_err or GenLoginApiError(f"Could not start profile {profile_id}")

    def stop_profile(self, profile_id: str) -> dict:
        """Explicit stop only — the app never calls this automatically.
        Official path GET /profiles/{id}/stop, legacy fallback."""
        last_err = None
        for path in (f"/profiles/{profile_id}/stop",
                     f"/profiles/stop/{profile_id}"):
            try:
                return self._request("GET", path)
            except GenLoginApiError as e:
                last_err = e
                if "HTTP 404" not in str(e):
                    raise
        raise last_err or GenLoginApiError(f"Could not stop profile {profile_id}")
