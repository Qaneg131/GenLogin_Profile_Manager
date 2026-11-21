"""Task Manager: persisted tasks, status, interrupted-task re-check
on restart (re-check state first, never blindly replay)."""
from __future__ import annotations
from PySide6.QtWidgets import (QLabel, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QHBoxLayout)


class TaskManagerPage(QWidget):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        lay = QVBoxLayout(self)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Kind", "Target", "Status", "Created"])
        lay.addWidget(self.table)
        btns = QHBoxLayout()
        b = QPushButton("Refresh"); b.clicked.connect(self.refresh); btns.addWidget(b)
        b2 = QPushButton("Check interrupted tasks"); b2.clicked.connect(self.check_interrupted); btns.addWidget(b2)
        lay.addLayout(btns)
        self.refresh()

    def refresh(self):
        repo = self.ctx.get("task_repo")
        tasks = repo.list_tasks() if repo else []
        self.table.setRowCount(len(tasks))
        for r, t in enumerate(tasks):
            for c, v in enumerate([t.id, t.kind, t.target_version or "", t.status, t.created_at]):
                self.table.setItem(r, c, QTableWidgetItem(v))

    def check_interrupted(self):
        repo = self.ctx.get("task_repo")
        if not repo:
            return
        interrupted = repo.interrupted_tasks()
        if not interrupted:
            QMessageBox.information(self, "Interrupted tasks", "No interrupted tasks.")
            return
        QMessageBox.information(
            self, "Interrupted tasks",
            f"{len(interrupted)} task(s) were left {', '.join(sorted({t.status for t in interrupted}))} "
            "when the app last exited.\n\nThey are NOT auto-resumed. "
            "Re-check each profile's live state in Profile Manager first, "
            "then re-run only the items still pending — never blindly replay "
            "an operation whose previous result is uncertain.")
        self.refresh()
