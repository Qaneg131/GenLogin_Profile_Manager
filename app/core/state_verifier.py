"""Verify resulting state — never report success from a sent request."""
from __future__ import annotations
import time


def verify_running(api, profile_id: str, timeout=30.0, poll=2.0) -> bool:
    """Poll getProfilesRunning()/get_profile until the profile is running
    or the timeout expires."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if api.is_running(profile_id):
                return True
        except Exception:
            pass
        time.sleep(poll)
    return False


def verify_version(api, profile_id: str, expected: str, timeout=30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            p = api.get_profile(profile_id)
            if p and p.browser_version == expected:
                return True
        except Exception:
            pass
        time.sleep(2.0)
    return False
