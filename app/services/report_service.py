"""CSV reports. Never includes cookies, passwords, proxy credentials,
tokens or any secret — only ids, names, versions, status, reason."""
from __future__ import annotations
import csv
from app.core.models import Task


def export_task_csv(task: Task, path: str) -> str:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["task_id", "kind", "profile_id", "profile_name", "status",
                    "reason", "attempts", "previous_version", "resulting_version"])
        for it in task.items:
            w.writerow([task.id, task.kind, it.profile_id, it.profile_name,
                        it.status, it.reason, it.attempts,
                        it.previous_version or "", it.resulting_version or ""])
    return path


def export_errors_csv(errors, path: str) -> str:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["task_id", "profile_id", "profile_name", "operation",
                    "timestamp", "message", "attempts", "screenshot_path", "resolution"])
        for e in errors:
            w.writerow([e.task_id or "", e.profile_id, e.profile_name, e.operation,
                        e.timestamp, e.message, e.attempts,
                        e.screenshot_path or "", e.resolution])
    return path
