from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
import json, subprocess, os

class Phase102Adapter:
    def __init__(self, root: Path):
        self.root = root
        self.ctl = root / "phase102_ceo_runtime_stack_integration_bundle" / "phase102_unified_runtime_ctl.py"

    def available(self) -> bool:
        return self.ctl.exists()

    def _run(self, args):
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{self.root}:{self.root / 'companyos'}"
        cp = subprocess.run(
            ["python", str(self.ctl), *args],
            cwd=str(self.root),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        out = (cp.stdout or "").strip()
        err = (cp.stderr or "").strip()
        parsed = None
        if out:
            try:
                parsed = json.loads(out)
            except Exception:
                pass
        return {
            "returncode": cp.returncode,
            "stdout": out,
            "stderr": err,
            "json": parsed,
        }

    def status(self) -> Dict[str, Any]:
        if not self.available():
            return {"available": False, "ready": False, "reason": "phase102_ctl_missing"}
        r = self._run(["status"])
        data = r.get("json") or {}
        return {
            "available": True,
            "ready": bool(data.get("unified_ready")),
            "data": data,
            "raw": r,
        }

    def start(self) -> Dict[str, Any]:
        if not self.available():
            return {"success": False, "reason": "phase102_ctl_missing"}
        return self._run([
            "start",
            "--financial-supervisor-interval", "15",
            "--watchdog-check-every", "30",
            "--financial-max-failures", "5",
            "--restart-backoff", "5",
            "--ceo-interval", "10",
            "--ceo-max-failures", "5",
        ])

    def stop(self) -> Dict[str, Any]:
        if not self.available():
            return {"success": False, "reason": "phase102_ctl_missing"}
        return self._run(["stop"])
