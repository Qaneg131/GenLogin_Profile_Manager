"""Dashboard: totals, running, task counts, CPU/RAM, recent activity."""
from __future__ import annotations
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from app.core.resource_monitor import ResourceMonitor


class DashboardPage(QWidget):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.monitor = ResourceMonitor(ctx["settings"].get("cpu_threshold_percent", 85),
                                       ctx["settings"].get("ram_threshold_percent", 85))
        lay = QVBoxLayout(self)
        self.lbl = QLabel("Loading…")
        lay.addWidget(self.lbl)
        self.refresh()

    def refresh(self):
        profiles = self.ctx.get("profiles", [])
        running = sum(1 for p in profiles if p.running)
        s = self.monitor.snapshot()
        cpu = f"{s['cpu']:.0f}%" if s.get("cpu") is not None else "n/a"
        ram = f"{s['ram']:.0f}%" if s.get("ram") is not None else "n/a"
        tasks = self.ctx.get("tasks", [])
        self.lbl.setText(
            f"Total profiles discovered: {len(profiles)}\n"
            f"Profiles selected: {len(self.ctx.get('selected_ids', []))}\n"
            f"Profiles currently running: {running}\n"
            f"Tasks: {len(tasks)}  |  CPU: {cpu}  RAM: {ram}\n"
            f"Base URL: {self.ctx['settings'].get('base_url')}\n"
            "Recent activity: see History & Reports. "
            "Live data loads from Profile Manager → Refresh.")
