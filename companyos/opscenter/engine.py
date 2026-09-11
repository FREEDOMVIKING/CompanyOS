from datetime import datetime, timezone
from pathlib import Path
import os

from .aggregator import OperationsAggregator
from .notifications import generate_notifications, persist_notifications
from .storage import atomic_write_json, read_json

class OperationsEngine:
    def __init__(self, home: Path | None = None):
        self.home = Path(home or os.environ.get("COMPANYOS_HOME", str(Path.home() / "companyos")))
        self.runtime = self.home / "companyos_runtime" / "opscenter"
        self.runtime.mkdir(parents=True, exist_ok=True)

    def run_cycle(self):
        snapshot = OperationsAggregator(self.home).snapshot()
        notices = generate_notifications(snapshot)
        history = persist_notifications(self.runtime / "notifications.json", notices)
        snapshot["notifications"] = list(reversed(history[-200:]))

        atomic_write_json(self.runtime / "latest_ops_snapshot.json", snapshot)

        history_path = self.runtime / "kpi_history.json"
        kpi_history = read_json(history_path, [])
        kpi_history.append(snapshot["kpis"])
        atomic_write_json(history_path, kpi_history[-1000:])

        return snapshot
