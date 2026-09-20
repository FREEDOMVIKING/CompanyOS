from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

from companyos.runtime.connector_readiness import ConnectorReadinessAudit
from companyos.runtime.launch_readiness import LaunchReadinessAudit
from companyos.runtime.runtime_control import UnifiedRuntimeControl


class EndToEndQualification:
    def __init__(self, root: Path | None = None):
        self.root = Path(root or (Path.home() / "companyos")).resolve()
        self.runtime_root = Path.home() / ".companyos_runtime"
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self.path = self.runtime_root / "full_autonomous_qualification.json"
        self.control = UnifiedRuntimeControl(self.root)

    def _dashboard_check(self):
        url = "http://127.0.0.1:8765/api/health"
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                obj = json.loads(response.read().decode("utf-8"))
            return {
                "ok": response.status == 200,
                "url": url,
                "runtime_healthy": bool(
                    (obj.get("health") or {}).get("healthy")
                ),
            }
        except Exception as exc:
            return {
                "ok": False,
                "url": url,
                "error": f"{type(exc).__name__}:{exc}",
            }

    def run(self, recovery_test=True):
        start = self.control.recover()
        health_before = self.control.health()
        dashboard = self._dashboard_check()
        launch = LaunchReadinessAudit(self.root).run()
        connectors = ConnectorReadinessAudit(self.root).run()

        recovery = {"tested": False, "ok": None}
        if recovery_test:
            recovery["tested"] = True
            stopped = self.control.stop(wait_seconds=45)
            restarted = self.control.recover()
            health_after = self.control.health()
            recovery.update(
                {
                    "ok": bool(
                        stopped.get("ok")
                        and restarted.get("ok")
                        and health_after.get("healthy")
                    ),
                    "stop": {"ok": stopped.get("ok"), "action": stopped.get("action")},
                    "restart": {
                        "ok": restarted.get("ok"),
                        "action": restarted.get("action"),
                    },
                    "health_after": health_after,
                }
            )
        else:
            health_after = self.control.health()

        core_checks = {
            "runtime_started": bool(start.get("ok")),
            "runtime_healthy": bool(health_before.get("healthy")),
            "dashboard_reachable": bool(dashboard.get("ok")),
            "launch_readiness": bool(launch.get("ready")),
            "recovery_passed": bool(recovery.get("ok"))
            if recovery_test
            else True,
        }

        core_pass = all(core_checks.values())
        configured = connectors.get("configured_count", 0)
        total = connectors.get("total_count", 0)
        live_finance = (
            connectors.get("connectors", {})
            .get("solana_wallet", {})
            .get("live_finance_enabled", False)
        )

        if core_pass and configured == total and live_finance:
            launch_level = "full_external_autonomy_configured"
        elif core_pass:
            launch_level = "core_autonomy_ready_external_connectors_partial"
        else:
            launch_level = "not_ready"

        result = {
            "qualified_at_unix": time.time(),
            "core_pass": core_pass,
            "launch_level": launch_level,
            "core_checks": core_checks,
            "dashboard": dashboard,
            "launch_readiness": launch,
            "connectors": connectors,
            "recovery": recovery,
            "final_health": health_after,
            "important": (
                "This qualification proves the continuous local CompanyOS "
                "control/recovery/dashboard stack. External actions are only "
                "available for connectors reported configured. Live financial "
                "execution remains gated by COMPANYOS_ENABLE_LIVE_FINANCE=1."
            ),
        }

        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(result, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )
        tmp.replace(self.path)
        return result
