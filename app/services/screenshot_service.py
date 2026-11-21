"""Screenshots on failure, organised screenshots/<task_id>/<profile_id>_<ts>.png.
Uses PySide6 screen grab when a GUI is present; otherwise records the
attempt and returns None (never fakes a screenshot)."""
from __future__ import annotations
import os
from datetime import datetime


def screenshot_path(base_dir: str, task_id: str, profile_id: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in profile_id)
    return os.path.join(base_dir, task_id, f"{safe}_{ts}.png")


def capture(base_dir: str, task_id: str, profile_id: str):
    """Try a real screen grab; return path or None."""
    path = screenshot_path(base_dir, task_id, profile_id)
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QGuiApplication
        app = QApplication.instance()
        if app is None:
            return None
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return None
        pix = screen.grabWindow(0)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        pix.save(path, "png")
        return path
    except Exception:
        return None
