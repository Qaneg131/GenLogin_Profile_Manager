"""Main window: left nav (8 sections, plan §5), stacked pages.
OPEN ONLY and UPDATE ONLY are separate pages to prevent accidents."""
from __future__ import annotations
from PySide6.QtWidgets import (QHBoxLayout, QListWidget, QMainWindow,
    QStackedWidget, QWidget)
from app.ui.dashboard import DashboardPage
from app.ui.profile_manager import ProfileManagerPage
from app.ui.bulk_open import BulkOpenPage
from app.ui.bulk_update import BulkUpdatePage
from app.ui.error_center import ErrorCenterPage
from app.ui.task_manager import TaskManagerPage
from app.ui.history import HistoryPage
from app.ui.settings import SettingsPage

PAGES = ["Dashboard", "Profile Manager", "Bulk Version Update", "Bulk Open",
         "Error Center", "Task Manager", "History & Reports", "Settings"]


class MainWindow(QMainWindow):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.setWindowTitle("GenLogin Profile Manager")
        self.resize(1100, 700)
        central = QWidget(); self.setCentralWidget(central)
        lay = QHBoxLayout(central)
        self.nav = QListWidget(); self.nav.addItems(PAGES)
        self.nav.setMaximumWidth(200)
        self.nav.currentRowChanged.connect(self._show)
        lay.addWidget(self.nav)
        self.stack = QStackedWidget()
        self.pages = [DashboardPage(ctx), ProfileManagerPage(ctx),
                      BulkUpdatePage(ctx), BulkOpenPage(ctx),
                      ErrorCenterPage(ctx), TaskManagerPage(ctx),
                      HistoryPage(ctx), SettingsPage(ctx)]
        for p in self.pages:
            self.stack.addWidget(p)
        lay.addWidget(self.stack, 1)
        self.nav.setCurrentRow(0)

    def _show(self, row):
        self.stack.setCurrentIndex(row)
        page = self.pages[row]
        if hasattr(page, "refresh"):
            page.refresh()
