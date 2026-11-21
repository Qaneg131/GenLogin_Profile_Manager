"""Error Center: per-profile failures, screenshot path, retry, export CSV."""
from __future__ import annotations
import os
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QFileDialog)
from app.services.report_service import export_errors_csv


class ErrorCenterPage(QWidget):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        lay = QVBoxLayout(self)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Profile", "Operation", "Time", "Message", "Attempts", "Screenshot"])
        lay.addWidget(self.table)
        btns = QHBoxLayout()
        for text, fn in [("Refresh", self.refresh), ("Open screenshot folder", self.open_folder),
                         ("Export failures CSV…", self.export)]:
            b = QPushButton(text); b.clicked.connect(fn); btns.addWidget(b)
        lay.addLayout(btns)
        self.refresh()

    def refresh(self):
        repo = self.ctx.get("error_repo")
        errors = repo.list_open() if repo else []
        self.errors = errors
        self.table.setRowCount(len(errors))
        for r, e in enumerate(errors):
            for c, v in enumerate([f"{e.profile_name} ({e.profile_id})", e.operation,
                                   e.timestamp, e.message[:200], str(e.attempts),
                                   e.screenshot_path or ""]):
                self.table.setItem(r, c, QTableWidgetItem(v))

    def open_folder(self):
        path = os.path.abspath(self.ctx["settings"].get("screenshot_dir", "screenshots"))
        os.makedirs(path, exist_ok=True)
        os.startfile(path) if os.name == "nt" else QMessageBox.information(self, "Screenshots", path)

    def export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export failures", "exports/failures.csv", "CSV (*.csv)")
        if path:
            export_errors_csv(self.errors, path)
            QMessageBox.information(self, "Exported", path)
