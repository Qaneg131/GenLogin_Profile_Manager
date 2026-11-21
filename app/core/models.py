"""Data models. Only fields actually returned by GenLogin are used;
unknown/missing fields stay None — never invented."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Profile:
    id: str
    name: str = ""
    group: Optional[str] = None
    browser_type: Optional[str] = None
    browser_version: Optional[str] = None
    running: bool = False
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_api(cls, data: dict) -> "Profile":
        pid = str(data.get("id") or data.get("profile_id") or "")
        # Browser version field name varies by build; try common keys.
        version = None
        pd = data.get("profile_data") or {}
        for key in ("browser_version", "browserVersion", "version",
                    "chrome_version", "core_version"):
            if data.get(key):
                version = str(data[key]); break
            if isinstance(pd, dict) and pd.get(key):
                version = str(pd[key]); break
        return cls(
            id=pid,
            name=str(data.get("name") or data.get("profile_name") or pid),
            group=data.get("group") or data.get("group_name"),
            browser_type=data.get("browser_type") or data.get("browser"),
            browser_version=version,
            running=bool(data.get("is_running") or data.get("running")
                         or data.get("status") == "running"),
            raw=dict(data),
        )


@dataclass
class TaskItem:
    profile_id: str
    profile_name: str = ""
    status: str = "pending"  # pending|running|success|failed|skipped
    reason: str = ""
    attempts: int = 0
    previous_version: Optional[str] = None
    resulting_version: Optional[str] = None


@dataclass
class Task:
    id: str
    kind: str  # open_only|update_only|update_open
    target_version: Optional[str] = None
    status: str = "pending"  # pending|running|paused|completed|failed|cancelled
    created_at: str = ""
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    items: list = field(default_factory=list)

    @property
    def success_count(self): return sum(1 for i in self.items if i.status == "success")
    @property
    def failed_count(self): return sum(1 for i in self.items if i.status == "failed")
    @property
    def skipped_count(self): return sum(1 for i in self.items if i.status == "skipped")


@dataclass
class ErrorRecord:
    profile_id: str
    profile_name: str = ""
    operation: str = ""  # load|update|launch|verification|screenshot
    timestamp: str = ""
    message: str = ""
    attempts: int = 1
    screenshot_path: Optional[str] = None
    resolution: str = "open"  # open|retried|resolved
    task_id: Optional[str] = None


def redact(text: str) -> str:
    """Strip anything that looks like a credential from log/report text."""
    if not text:
        return ""
    import re
    text = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._\-]+", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)(token\s*[:=]\s*)['\"]?[A-Za-z0-9._\-]{8,}", r"\1[REDACTED]", text)
    return text
