"""Settings: base URL (default 127.0.0.1:8787, alt localhost:55550),
concurrency/delay/timeout/retry, screenshots, log retention, theme,
resource thresholds, Test Connection."""
from __future__ import annotations
import json
from PySide6.QtWidgets import (QComboBox, QFormLayout, QLabel, QMessageBox,
    QPushButton, QSpinBox, QVBoxLayout, QWidget, QLineEdit)
from app.core.validators import validate_base_url, validate_concurrency


class SettingsPage(QWidget):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        s = ctx["settings"]
        lay = QVBoxLayout(self)
        form = QFormLayout()
        self.base_url = QLineEdit(s.get("base_url", "http://127.0.0.1:8787/"))
        form.addRow("GenLogin base URL:", self.base_url)
        self.alt = QLabel("Alternative (classic GenLogin): http://localhost:55550/ — "
                          "paste it above if 8787 is not GenLogin on your PC.")
        form.addRow("", self.alt)
        self.conc = QSpinBox(); self.conc.setRange(1, 20); self.conc.setValue(s.get("concurrency", 5))
        form.addRow("Default concurrency (1–20):", self.conc)
        self.delay = QSpinBox(); self.delay.setRange(0, 60); self.delay.setValue(int(s.get("delay_seconds", 1)))
        form.addRow("Delay between launches (s):", self.delay)
        self.timeout = QSpinBox(); self.timeout.setRange(10, 600); self.timeout.setValue(s.get("launch_timeout_seconds", 180))
        form.addRow("Launch timeout (s):", self.timeout)
        self.theme = QComboBox(); self.theme.addItems(["light", "dark"])
        self.theme.setCurrentText(s.get("theme", "light"))
        form.addRow("Theme:", self.theme)
        lay.addLayout(form)
        self.result = QLabel(""); lay.addWidget(self.result)
        for text, fn in [("Test Connection", self.test), ("Save settings", self.save)]:
            b = QPushButton(text); b.clicked.connect(fn); lay.addWidget(b)

    def test(self):
        try:
            url = validate_base_url(self.base_url.text())
        except ValueError as e:
            QMessageBox.warning(self, "Invalid URL", str(e)); return
        from app.integrations.genlogin_api import GenLoginApi
        api = GenLoginApi(url)
        r = api.test_connection()
        self.result.setText(str(r))
        QMessageBox.information(self, "Test Connection",
            "OK — GenLogin answered." if r.get("ok") else f"Failed: {r.get('error')}")

    def save(self):
        try:
            s = self.ctx["settings"]
            s["base_url"] = validate_base_url(self.base_url.text())
            s["concurrency"] = validate_concurrency(self.conc.value())
            s["delay_seconds"] = self.delay.value()
            s["launch_timeout_seconds"] = self.timeout.value()
            s["theme"] = self.theme.currentText()
            with open("config/settings.json", "w", encoding="utf-8") as f:
                json.dump(s, f, indent=2)
            QMessageBox.information(self, "Saved", "Settings saved to config/settings.json")
        except ValueError as e:
            QMessageBox.warning(self, "Invalid setting", str(e))
