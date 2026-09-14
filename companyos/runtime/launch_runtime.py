from __future__ import annotations

from pathlib import Path

from companyos.runtime.launch_gate import LaunchGate
from companyos.runtime.runtime_control import UnifiedRuntimeControl


class CompanyOSLaunchRuntime:
    def __init__(self, root: Path | None = None):
        self.root = Path(root or (Path.home() / "companyos")).resolve()
        self.control = UnifiedRuntimeControl(self.root)
        self.gate = LaunchGate(self.root)

    def start(self):
        recovered = self.control.recover()
        gate = self.gate.evaluate()
        return {
            "ok": bool(recovered.get("ok") and gate.get("allowed")),
            "runtime": recovered,
            "launch_gate": gate,
        }

    def stop(self):
        return self.control.stop()

    def status(self):
        return {
            "health": self.control.health(),
            "launch_gate": self.gate.evaluate(),
        }
