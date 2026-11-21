"""Bulk Open — OPEN ONLY.

Strictly read/launch-only: calls runProfile, then VERIFIES the profile
is actually running (state_verifier). Never edits profile settings,
never closes profiles, skips already-running, dedupes via TaskQueue.
"""
from __future__ import annotations
import time
from datetime import datetime

from app.core.models import ErrorRecord, TaskItem
from app.core.state_verifier import verify_running
from app.core.task_queue import TaskQueue
from app.services.screenshot_service import capture


class LaunchService:
    def __init__(self, api, db_errors=None, screenshot_dir="screenshots",
                 concurrency=5, delay=1.0, launch_timeout=180,
                 verify_timeout=30, retries=2, stop_on_error=False):
        self.api = api
        self.db_errors = db_errors
        self.screenshot_dir = screenshot_dir
        self.concurrency = concurrency
        self.delay = delay
        self.launch_timeout = launch_timeout
        self.verify_timeout = verify_timeout
        self.retries = retries
        self.stop_on_error = stop_on_error
        self.queue = TaskQueue(max_workers=concurrency)

    def open_profiles(self, items: list[TaskItem], task_id: str,
                      on_progress=None, monitor=None) -> list[TaskItem]:
        # Snapshot running set once, so already-running profiles are skipped.
        try:
            running_ids = {p.id for p in self.api.list_running()}
        except Exception:
            running_ids = set()

        def worker(item: TaskItem):
            if item.profile_id in running_ids:
                item.status, item.reason = "skipped", "Already running"
                return item.status
            if not self.queue.claim(item.profile_id):
                item.status, item.reason = "skipped", "Duplicate launch request"
                return item.status
            try:
                if monitor is not None:
                    paused, why = monitor.should_pause()
                    if paused:
                        # Wait for resources, do not kill anything.
                        time.sleep(2.0)
                for attempt in range(1, self.retries + 2):
                    item.attempts = attempt
                    try:
                        self.api.run_profile(item.profile_id)
                        break
                    except Exception as e:
                        if attempt > self.retries:
                            raise e
                        time.sleep(2.0)
                if verify_running(self.api, item.profile_id,
                                  timeout=self.verify_timeout):
                    item.status, item.reason = "success", "Verified running"
                else:
                    raise TimeoutError(
                        f"Launch request sent but profile not verified running "
                        f"within {self.verify_timeout}s")
            except Exception as e:  # noqa: BLE001
                item.status, item.reason = "failed", str(e)[:500]
                shot = capture(self.screenshot_dir, task_id, item.profile_id)
                if self.db_errors is not None:
                    self.db_errors.add(ErrorRecord(
                        task_id=task_id, profile_id=item.profile_id,
                        profile_name=item.profile_name, operation="launch",
                        timestamp=datetime.now().isoformat(), message=item.reason,
                        attempts=item.attempts, screenshot_path=shot))
                if self.stop_on_error:
                    self.queue.stop()
            finally:
                self.queue.release(item.profile_id)
            time.sleep(self.delay)
            return item.status

        self.queue.run_items(items, worker, on_progress=on_progress)
        return items
