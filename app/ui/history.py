"""History & Reports: search tasks, duration, CSV export (no secrets)."""
from __future__ import annotations
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)
from app.services.report_service import export_task_csv
from app.core.models import Task


class HistoryPage(QWidget):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        lay = QVBoxLayout(self)
        self.search = QLineEdit(); self.search.setPlaceholderText("Search by date / operation / status…")
        self.search.textChanged.connect(self.refresh)
        lay.addWidget(self.search)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Kind", "Status", "Start", "End", "Target"])
        lay.addWidget(self.table)
        btns = QHBoxLayout()
        b = QPushButton("Refresh"); b.clicked.connect(self.refresh); btns.addWidget(b)
        lay.addLayout(btns)
        self.refresh()

    def refresh(self):
        repo = self.ctx.get("task_repo")
        tasks = repo.list_tasks() if repo else []
        q = self.search.text().strip().lower()
        if q:
            tasks = [t for t in tasks if q in (t.kind + t.status + (t.created_at or "")).lower()]
        self.table.setRowCount(len(tasks))
        for r, t in enumerate(tasks):
            for c, v in enumerate([t.id, t.kind, t.status, t.started_at or "",
                                   t.ended_at or "", t.target_version or ""]):
                self.table.setItem(r, c, QTableWidgetItem(v))
