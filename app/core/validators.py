"""Input validation. No silent defaults for dangerous values."""
from __future__ import annotations
import re
from urllib.parse import urlparse


def validate_base_url(url: str) -> str:
    url = (url or "").strip().rstrip("/")
    if not url:
        raise ValueError("Base URL is empty.")
    p = urlparse(url if "://" in url else "http://" + url)
    if p.scheme not in ("http", "https"):
        raise ValueError("Base URL must be http(s).")
    if p.hostname not in ("127.0.0.1", "localhost"):
        raise ValueError("Base URL must be local (127.0.0.1 or localhost) — "
                         "the GenLogin Local API only runs on the same PC.")
    return f"{p.scheme}://{p.netloc}"


def validate_target_version(v: str) -> str:
    v = (v or "").strip()
    if not re.fullmatch(r"\d{2,3}(\.\d+)*", v):
        raise ValueError(f"Invalid browser version {v!r}: expected e.g. '156'.")
    return v


def validate_concurrency(n, max_concurrency: int = 20) -> int:
    n = int(n)
    if n < 1 or n > max_concurrency:
        raise ValueError(f"Concurrency must be 1..{max_concurrency}.")
    return n


def parse_id_list(text: str) -> list[str]:
    """Parse TXT/CSV pasted or imported profile IDs, one per line/comma."""
    ids, seen = [], set()
    for part in re.split(r"[\s,;]+", text or ""):
        part = part.strip()
        if part and part not in seen:
            seen.add(part); ids.append(part)
    return ids
