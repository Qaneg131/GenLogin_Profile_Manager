"""GenLogin Profile Manager — entry point (Windows).

Run from the project root:
    python -m app.main
Requires GenLogin running on THIS PC. Base URL defaults to
http://127.0.0.1:8787/ (config/settings.json); classic GenLogin is
http://localhost:55550/.
"""
from __future__ import annotations
import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_settings(path="config/settings.json") -> dict:
    defaults = {"base_url": "http://127.0.0.1:8787/", "concurrency": 5,
                "delay_seconds": 1.0, "launch_timeout_seconds": 180,
                "verify_timeout_seconds": 30, "retry_count": 2,
                "page_size": 100, "theme": "light",
                "cpu_threshold_percent": 85, "ram_threshold_percent": 85}
    try:
        with open(path, encoding="utf-8") as f:
            defaults.update(json.load(f))
    except FileNotFoundError:
        pass
    return defaults


def setup_logging(log_dir="logs", retention_days=30):
    os.makedirs(log_dir, exist_ok=True)
    h = RotatingFileHandler(os.path.join(log_dir, "application.log"),
                            maxBytes=5 * 1024 * 1024, backupCount=5)
    logging.basicConfig(level=logging.INFO, handlers=[h],
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def build_context(settings):
    from app.core.resource_monitor import ResourceMonitor
    from app.integrations.genlogin_api import GenLoginApi
    from app.storage.database import connect
    from app.storage.repositories import ErrorRepository, TaskRepository
    conn = connect("data/app.db")
    return {"settings": settings,
            "api": GenLoginApi(settings["base_url"]),
            "monitor": ResourceMonitor(settings.get("cpu_threshold_percent", 85),
                                       settings.get("ram_threshold_percent", 85)),
            "task_repo": TaskRepository(conn),
            "error_repo": ErrorRepository(conn),
            "profiles": [], "selected_ids": [], "tasks": []}


def main():
    settings = load_settings()
    setup_logging()
    logging.getLogger(__name__).info("Starting GenLogin Profile Manager, base_url=%s",
                                     settings["base_url"])
    from PySide6.QtWidgets import QApplication, QMessageBox
    from app.ui.main_window import MainWindow
    app = QApplication(sys.argv)
    ctx = build_context(settings)
    # Safe restart: flag interrupted tasks, do NOT auto-resume.
    interrupted = ctx["task_repo"].interrupted_tasks()
    win = MainWindow(ctx)
    win.show()
    if interrupted:
        QMessageBox.information(
            win, "Interrupted tasks",
            f"{len(interrupted)} task(s) were interrupted by a previous exit. "
            "Check Task Manager — re-verify profile state before resuming.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
