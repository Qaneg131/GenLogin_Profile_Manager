"""Profile Manager: paginated table, search/filter, multi-select,
import IDs, export CSV, refresh from the Local API."""
from __future__ import annotations
from PySide6.QtWidgets import (QComboBox, QFileDialog, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget)
from PySide6.QtCore import Qt
from app.services.profile_service import (export_profiles_csv, paginate,
    search_filter)
from app.core.validators import parse_id_list


class ProfileManagerPage(QWidget):
    COLS = ["ID", "Name", "Group", "Browser", "Version", "Status"]

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.page, self.filtered = 1, []
        lay = QVBoxLayout(self)
        top = QHBoxLayout()
        self.search = QLineEdit(); self.search.setPlaceholderText("Search name or ID…")
        self.search.textChanged.connect(self.apply_filter)
        self.group_cb = QComboBox(); self.group_cb.addItem("All groups")
        self.group_cb.currentTextChanged.connect(self.apply_filter)
        self.status_cb = QComboBox(); self.status_cb.addItems(["All", "running", "stopped"])
        self.status_cb.currentTextChanged.connect(self.apply_filter)
        top.addWidget(self.search); top.addWidget(self.group_cb); top.addWidget(self.status_cb)
        lay.addLayout(top)
        self.table = QTableWidget(0, len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.setSelectionMode(self.table.SelectionMode.MultiSelection)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self._on_select)
        lay.addWidget(self.table)
        btns = QHBoxLayout()
        self.conn_lbl = QLabel("Not connected")
        for text, fn in [("Refresh", self.refresh), ("Prev", self.prev_page),
                         ("Next", self.next_page), ("Select page", self.select_page),
                         ("Import IDs…", self.import_ids), ("Export CSV…", self.export_csv)]:
            b = QPushButton(text); b.clicked.connect(fn); btns.addWidget(b)
        btns.addWidget(self.conn_lbl)
        lay.addLayout(btns)
        self.page_lbl = QLabel("Page 1/1"); lay.addWidget(self.page_lbl)

    def _on_select(self):
        ids = {self.table.item(r, 0).text() for r in
               {i.row() for i in self.table.selectedItems()}}
        self.ctx["selected_ids"] = sorted(ids)

    def refresh(self):
        try:
            profiles = self.ctx["api"].list_all_profiles(
                page_size=self.ctx["settings"].get("page_size", 100))
            self.ctx["profiles"] = profiles
            self.conn_lbl.setText(f"Connected — {len(profiles)} profiles")
        except Exception as e:
            self.conn_lbl.setText(f"Connection error: {e}")
            QMessageBox.warning(self, "Connection error", str(e))
            return
        groups = sorted({p.group for p in self.ctx["profiles"] if p.group})
        self.group_cb.clear(); self.group_cb.addItem("All groups"); self.group_cb.addItems(groups)
        self.apply_filter()

    def apply_filter(self):
        group = None if self.group_cb.currentText() == "All groups" else self.group_cb.currentText()
        status = None if self.status_cb.currentText() == "All" else self.status_cb.currentText()
        self.filtered = search_filter(self.ctx.get("profiles", []),
                                      self.search.text(), group, None, status)
        self.page = 1; self.render()

    def render(self):
        page_items, total = paginate(self.filtered, self.page,
                                     self.ctx["settings"].get("page_size", 100))
        self.table.setRowCount(len(page_items))
        for r, p in enumerate(page_items):
            for c, v in enumerate([p.id, p.name, p.group or "", p.browser_type or "",
                                   p.browser_version or "", "running" if p.running else "stopped"]):
                self.table.setItem(r, c, QTableWidgetItem(v))
        self.page_lbl.setText(f"Page {self.page}/{max(1, total)} — {len(self.filtered)} filtered")

    def prev_page(self):
        self.page = max(1, self.page - 1); self.render()
    def next_page(self):
        self.page += 1; self.render()
    def select_page(self):
        self.table.selectAll(); self._on_select()
    def import_ids(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import profile IDs", "", "Text/CSV (*.txt *.csv)")
        if not path: return
        with open(path, encoding="utf-8") as f:
            ids = parse_id_list(f.read())
        self.ctx["selected_ids"] = ids
        QMessageBox.information(self, "Imported", f"{len(ids)} profile IDs imported.")
    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "exports/profiles.csv", "CSV (*.csv)")
        if path:
            export_profiles_csv(self.ctx.get("profiles", []), path)
            QMessageBox.information(self, "Exported", path)
