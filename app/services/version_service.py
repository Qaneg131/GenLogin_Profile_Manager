"""Bulk Version Update — preview + dry-run + audit ONLY, for now.

The browser-version update endpoint is UNCONFIRMED (see
docs/INTEGRATION_FINDINGS.md). No guessed HTTP call is made anywhere.
update_profile() raises UpdateNotSupportedError with instructions.
When the official method is confirmed, implement it here — and only
here — behind the same preview/verify/audit flow.
"""
from __future__ import annotations
from app.core.models import Profile, TaskItem


class UpdateNotSupportedError(NotImplementedError):
    pass


UPDATE_GATE_MESSAGE = (
    "Browser-version update is NOT enabled: no documented GenLogin "
    "endpoint for updating a profile's browser version was found in the "
    "public API docs (see docs/INTEGRATION_FINDINGS.md). "
    "Open http://127.0.0.1:8787/api-docs on the PC where GenLogin runs "
    "(or http://localhost:55550/api-docs) and confirm the update endpoint, "
    "request body and whether the profile must be stopped first. "
    "Preview and Dry Run below are safe — they change nothing."
)


def preview_update(profiles: list[Profile], target_version: str,
                   running_ids: set[str]) -> list[TaskItem]:
    """Classify every selected profile without changing anything."""
    items = []
    for p in profiles:
        it = TaskItem(profile_id=p.id, profile_name=p.name,
                      previous_version=p.browser_version)
        if p.id in running_ids:
            it.status, it.reason = "skipped", "Running — stop confirmation required before any update"
        elif p.browser_version == target_version:
            it.status, it.reason = "skipped", f"Already at {target_version}"
        elif p.browser_version is None:
            it.status, it.reason = "skipped", "Current version unknown — cannot verify update"
        else:
            it.status, it.reason = "pending", f"Needs update {p.browser_version} -> {target_version}"
        items.append(it)
    return items


def dry_run(items: list[TaskItem]) -> list[TaskItem]:
    """Dry Run: classify only, perform no changes, mark what WOULD happen."""
    for it in items:
        if it.status == "pending":
            it.status, it.reason = "skipped", "Dry run — no change made: " + it.reason
    return items


def update_profile(api, item: TaskItem, target_version: str) -> TaskItem:
    """GATED — do not call a guessed endpoint. Raises until confirmed."""
    raise UpdateNotSupportedError(UPDATE_GATE_MESSAGE)


def update_and_open(api, launch_service, items, target_version, task_id):
    """Update + Open workflow, as far as the gate allows: update step
    raises, so nothing is launched on an unverified update. When the
    update path is confirmed, this launches only verified-success items."""
    updated = []
    for it in items:
        if it.status != "pending":
            continue
        update_profile(api, it, target_version)  # raises today
        updated.append(it)
    return launch_service.open_profiles(updated, task_id)
