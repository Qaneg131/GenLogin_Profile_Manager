"""Bounded, pausable task queue. Runs work in a background thread so the
GUI never blocks. Prevents two tasks touching the same profile at once."""
from __future__ import annotations
import threading
import time
from typing import Callable


class TaskQueue:
    def __init__(self, max_workers: int = 5):
        self.max_workers = max(1, int(max_workers))
        self._lock = threading.Lock()
        self._paused = threading.Event()  # set = paused
        self._stop = threading.Event()
        self._active_profiles: set[str] = set()
        self._sem = threading.Semaphore(self.max_workers)

    def pause(self): self._paused.set()
    def resume(self): self._paused.clear()
    def stop(self): self._stop.set(); self._paused.clear()
    @property
    def stopped(self): return self._stop.is_set()

    def claim(self, profile_id: str) -> bool:
        """Dedupe: False if this profile is already being processed."""
        with self._lock:
            if profile_id in self._active_profiles:
                return False
            self._active_profiles.add(profile_id)
            return True

    def release(self, profile_id: str):
        with self._lock:
            self._active_profiles.discard(profile_id)

    def wait_if_paused(self):
        while self._paused.is_set() and not self._stop.is_set():
            time.sleep(0.2)

    def run_items(self, items, worker: Callable, on_progress=None):
        """Run worker(item) for each item with bounded concurrency.
        worker must be idempotent-safe; failures never stop other items
        unless the queue itself is stopped."""
        threads = []
        results = {}

        def _run(item):
            with self._sem:
                if self._stop.is_set():
                    results[item.profile_id] = "cancelled"; return
                self.wait_if_paused()
                try:
                    results[item.profile_id] = worker(item)
                except Exception as e:  # noqa: BLE001 - record, continue
                    results[item.profile_id] = f"failed: {e}"
                if on_progress:
                    on_progress(item)

        for it in items:
            t = threading.Thread(target=_run, args=(it,), daemon=True)
            threads.append(t); t.start()
        for t in threads:
            t.join()
        return results
