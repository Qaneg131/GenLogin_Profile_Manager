"""Profile loading / search / filter / import / export (read-only)."""
from __future__ import annotations
import csv
from app.core.models import Profile
from app.core.validators import parse_id_list


def search_filter(profiles, query="", group=None, version=None, status=None):
    q = (query or "").strip().lower()
    out = []
    for p in profiles:
        if q and q not in p.name.lower() and q not in p.id.lower():
            continue
        if group and p.group != group:
            continue
        if version and p.browser_version != version:
            continue
        if status == "running" and not p.running:
            continue
        if status == "stopped" and p.running:
            continue
        out.append(p)
    return out


def paginate(items, page: int, page_size: int):
    page = max(1, page)
    start = (page - 1) * page_size
    return items[start:start + page_size], (len(items) + page_size - 1) // page_size


def import_ids_from_text(text: str) -> list[str]:
    return parse_id_list(text)


def export_profiles_csv(profiles: list[Profile], path: str) -> str:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "name", "group", "browser_type", "browser_version", "running"])
        for p in profiles:
            w.writerow([p.id, p.name, p.group or "", p.browser_type or "",
                        p.browser_version or "", "running" if p.running else "stopped"])
    return path
