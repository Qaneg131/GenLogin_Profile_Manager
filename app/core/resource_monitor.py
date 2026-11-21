"""Smart Queue resource monitor. Conservative: pause launching NEW
profiles over threshold, never terminate running profiles."""
from __future__ import annotations
try:
    import psutil
except Exception:  # psutil optional on the test VM
    psutil = None


class ResourceMonitor:
    def __init__(self, cpu_threshold=85.0, ram_threshold=85.0):
        self.cpu_threshold = cpu_threshold
        self.ram_threshold = ram_threshold

    def snapshot(self) -> dict:
        if psutil is None:
            return {"cpu": None, "ram": None, "available": False}
        return {"cpu": psutil.cpu_percent(interval=0.1),
                "ram": psutil.virtual_memory().percent, "available": True}

    def should_pause(self) -> tuple[bool, str]:
        s = self.snapshot()
        if not s["available"]:
            return False, "Resource monitor unavailable (psutil missing); queue runs on configured concurrency only."
        if s["cpu"] is not None and s["cpu"] > self.cpu_threshold:
            return True, f"CPU {s['cpu']:.0f}% > {self.cpu_threshold:.0f}% threshold"
        if s["ram"] is not None and s["ram"] > self.ram_threshold:
            return True, f"RAM {s['ram']:.0f}% > {self.ram_threshold:.0f}% threshold"
        return False, ""
