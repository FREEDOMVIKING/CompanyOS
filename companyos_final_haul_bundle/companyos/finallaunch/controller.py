from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
import json, os, subprocess, time

from companyos.canonicalproduction import CanonicalProductionRuntime

from .profiles import safe_profile, trial_profile, full_profile

CONFIRM_TRIAL = "I_UNDERSTAND_TRIAL_LIVE"
CONFIRM_FULL = "I_UNDERSTAND_FULL_LIVE"

class FinalLaunchController:
    def __init__(self, companyos_root: str | None = None):
        self.root = Path(companyos_root or os.environ.get(
            "COMPANYOS_ROOT", str(Path.home() / "companyos")
        ))
        self.runtime = self.root / "companyos_runtime" / "final_launch"
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.profile_file = self.runtime / "launch_profile.json"
        self.audit_file = self.runtime / "launch_audit.jsonl"
        self.production = CanonicalProductionRuntime(str(self.root))

    def _write_profile(self, profile: Dict[str, Any]) -> None:
        tmp = self.profile_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(profile, indent=2, sort_keys=True))
        tmp.replace(self.profile_file)

    def _audit(self, event: str, data: Dict[str, Any]) -> None:
        with self.audit_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": time.time(),
                "event": event,
                "data": data,
            }, sort_keys=True) + "\n")

    def current_profile(self) -> Dict[str, Any]:
        if not self.profile_file.exists():
            p = safe_profile().to_dict()
            self._write_profile(p)
            return p
        try:
            return json.loads(self.profile_file.read_text())
        except Exception:
            p = safe_profile().to_dict()
            self._write_profile(p)
            return p

    def preflight(self) -> Dict[str, Any]:
        required = {
            "bundle1_gateway": self.root/"companyos"/"canonicalexec"/"gateway.py",
            "bundle2_orchestration": self.root/"companyos"/"canonicalorchestration"/"bridge.py",
            "bundle3_runtime_bridge": self.root/"companyos"/"canonicalruntime"/"bridge.py",
            "bundle4_production": self.root/"companyos"/"canonicalproduction"/"controller.py",
            "bundle5_daemon": self.root/"companyos"/"canonicaldaemon"/"daemon.py",
            "service_script": self.root/"scripts"/"companyos_service.sh",
            "phase102_ctl": self.root/"phase102_ceo_runtime_stack_integration_bundle"/"phase102_unified_runtime_ctl.py",
        }
        files_ok = {k: p.exists() for k,p in required.items()}

        prod = self.production.status()
        service = subprocess.run(
            ["bash", str(self.root/"scripts"/"companyos_service.sh"), "status"],
            cwd=str(self.root),
            capture_output=True,
            text=True,
        )

        out = {
            "files": files_ok,
            "files_ok": all(files_ok.values()),
            "production_status": prod,
            "service_status": service.stdout.strip(),
            "service_running": "COMPANYOS_SERVICE_RUNNING" in service.stdout,
            "current_profile": self.current_profile(),
        }
        out["preflight_pass"] = bool(out["files_ok"] and prod.get("execution_gateway", {}).get("ready"))
        self._audit("preflight", out)
        return out

    def set_safe(self) -> Dict[str, Any]:
        p = safe_profile().to_dict()
        self._write_profile(p)
        self._audit("profile_safe", p)
        return p

    def set_trial(self, max_single: float, max_daily: float, confirm: str) -> Dict[str, Any]:
        if confirm != CONFIRM_TRIAL:
            raise ValueError("trial confirmation token incorrect")
        if max_single <= 0 or max_daily <= 0 or max_single > max_daily:
            raise ValueError("invalid trial limits")
        p = trial_profile(max_single, max_daily).to_dict()
        self._write_profile(p)
        self._audit("profile_trial_live", p)
        return p

    def set_full(self, max_single: float, max_daily: float, max_failures: int, confirm: str) -> Dict[str, Any]:
        if confirm != CONFIRM_FULL:
            raise ValueError("full-live confirmation token incorrect")
        if max_single <= 0 or max_daily <= 0 or max_single > max_daily:
            raise ValueError("invalid full-live limits")
        if max_failures < 1:
            raise ValueError("max_failures must be >= 1")
        p = full_profile(max_single, max_daily, max_failures).to_dict()
        self._write_profile(p)
        self._audit("profile_full_live", p)
        return p
