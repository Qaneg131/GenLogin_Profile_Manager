"""Bulk Open — OPEN ONLY. Visually separate from Bulk Update.
Runs in a background thread; Stop / Pause / Resume controls."""
from __future__ import annotations
import threading
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QMessageBox,
    QProgressBar, QPushButton, QSpinBox, QVBoxLayout, QWidget)
from PySide6.QtCore import Qt
from app.core.models import TaskItem
from app.services.launch_service import LaunchService


class BulkOpenPage(QWidget):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx; self.service = None; self.thread = None
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("OPEN ONLY — launches selected profiles WITHOUT changing "
                             "version or any other setting."))
        row = QHBoxLayout()
        row.addWidget(QLabel("Concurrency:"))
        self.conc = QComboBox(); self.conc.addItems(["1", "2", "5", "10", "20"])
        self.conc.setCurrentText(str(ctx["settings"].get("concurrency", 5)))
        self.delay = QSpinBox(); self.delay.setRange(0, 60)
        self.delay.setValue(int(ctx["settings"].get("delay_seconds", 1)))
        row.addWidget(self.conc); row.addWidget(QLabel("Delay (s):")); row.addWidget(self.delay)
        lay.addLayout(row)
        self.progress = QProgressBar(); lay.addWidget(self.progress)
        self.status = QLabel("Idle — select profiles in Profile Manager first.")
        lay.addWidget(self.status)
        btns = QHBoxLayout()
        self.btn_open = QPushButton("OPEN ONLY"); self.btn_open.clicked.connect(self.start)
        self.btn_pause = QPushButton("Pause"); self.btn_pause.clicked.connect(self.pause)
        self.btn_resume = QPushButton("Resume"); self.btn_resume.clicked.connect(self.resume)
        self.btn_stop = QPushButton("Stop"); self.btn_stop.clicked.connect(self.stop)
        for b in (self.btn_open, self.btn_pause, self.btn_resume, self.btn_stop):
            btns.addWidget(b)
        lay.addLayout(btns)

    def _selected_items(self):
        by_id = {p.id: p for p in self.ctx.get("profiles", [])}
        return [TaskItem(profile_id=i, profile_name=by_id[i].name if i in by_id else i)
                for i in self.ctx.get("selected_ids", [])]

    def start(self):
        items = self._selected_items()
        if not items:
            QMessageBox.warning(self, "Nothing selected", "Select profiles in Profile Manager first.")
            return
        if QMessageBox.question(self, "Confirm OPEN ONLY",
                f"Launch {len(items)} profile(s) without changing any settings?") != QMessageBox.StandardButton.Yes:
            return
        s = self.ctx["settings"]
        self.service = LaunchService(self.ctx["api"], self.ctx.get("error_repo"),
            concurrency=int(self.conc.currentText()), delay=self.delay.value(),
            launch_timeout=s.get("launch_timeout_seconds", 180),
            verify_timeout=s.get("verify_timeout_seconds", 30),
            retries=s.get("retry_count", 2), stop_on_error=s.get("stop_on_error", False))
        self.progress.setMaximum(len(items)); self.progress.setValue(0)
        self.status.setText(f"Opening {len(items)} profiles…")
        def run():
            done = [0]
            def prog(_):
                done[0] += 1; self.progress.setValue(done[0])
            self.service.open_profiles(items, task_id="ui-open", on_progress=prog,
                                       monitor=self.ctx.get("monitor"))
            ok = sum(1 for i in items if i.status == "success")
            sk = sum(1 for i in items if i.status == "skipped")
            fa = sum(1 for i in items if i.status == "failed")
            self.status.setText(f"Done: {ok} opened, {sk} skipped, {fa} failed. See Error Center for failures.")
        self.thread = threading.Thread(target=run, daemon=True); self.thread.start()

    def pause(self):
        if self.service: self.service.queue.pause(); self.status.setText("Paused.")
    def resume(self):
        if self.service: self.service.queue.resume(); self.status.setText("Resumed.")
    def stop(self):
        if self.service: self.service.queue.stop(); self.status.setText("Stopping…")
