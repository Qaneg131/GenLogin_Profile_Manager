"""Bulk Version Update — preview + dry-run + audit.
The WRITE path is GATED (see services/version_service.py): the Execute
button stays disabled until the official update endpoint is confirmed.
Update + Open is shown here too, with the same gate."""
from __future__ import annotations
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QTextEdit, QVBoxLayout, QWidget)
from app.core.validators import validate_target_version
from app.services.version_service import (UPDATE_GATE_MESSAGE, dry_run,
    preview_update, update_profile, UpdateNotSupportedError)


class BulkUpdatePage(QWidget):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx; self.items = []
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("UPDATE ONLY — preview and Dry Run only. "
                             "The write path is DISABLED until the official update "
                             "endpoint is confirmed (see docs/INTEGRATION_FINDINGS.md)."))
        row = QHBoxLayout(); row.addWidget(QLabel("Target browser version (e.g. 156):"))
        self.version = QLineEdit("156"); row.addWidget(self.version); lay.addLayout(row)
        self.out = QTextEdit(); self.out.setReadOnly(True); lay.addWidget(self.out)
        btns = QHBoxLayout()
        self.btn_preview = QPushButton("Preview"); self.btn_preview.clicked.connect(self.preview)
        self.btn_dry = QPushButton("Dry Run"); self.btn_dry.clicked.connect(self.do_dry_run)
        self.btn_exec = QPushButton("Execute Update (disabled — unconfirmed endpoint)")
        self.btn_exec.setEnabled(False); self.btn_exec.clicked.connect(self.execute)
        self.btn_update_open = QPushButton("Update + Open (disabled — same gate)")
        self.btn_update_open.setEnabled(False); self.btn_update_open.clicked.connect(self.execute)
        for b in (self.btn_preview, self.btn_dry, self.btn_exec, self.btn_update_open):
            btns.addWidget(b)
        lay.addLayout(btns)
        self.out.setPlainText(UPDATE_GATE_MESSAGE)

    def _profiles(self):
        by_id = {p.id: p for p in self.ctx.get("profiles", [])}
        return [by_id[i] for i in self.ctx.get("selected_ids", []) if i in by_id]

    def preview(self):
        try:
            target = validate_target_version(self.version.text())
        except ValueError as e:
            QMessageBox.warning(self, "Invalid version", str(e)); return
        running = {p.id for p in self.ctx.get("profiles", []) if p.running}
        self.items = preview_update(self._profiles(), target, running)
        lines = [f"{i.profile_name} ({i.profile_id}): {i.status} — {i.reason}" for i in self.items]
        self.out.setPlainText("\n".join(lines) or "No profiles selected.")

    def do_dry_run(self):
        self.preview()
        dry_run(self.items)
        self.out.setPlainText("\n".join(
            f"{i.profile_name}: {i.status} — {i.reason}" for i in self.items)
            + "\n\nDry Run complete — no changes were made.")

    def execute(self):
        QMessageBox.warning(self, "Update disabled", UPDATE_GATE_MESSAGE)
