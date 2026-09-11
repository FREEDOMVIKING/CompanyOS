from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from companyos.walletintegration.reconciliation_worker import PendingReconciliationWorker


class CompanyOSHealthSupervisor:
    """
    Phase 68 V2 startup/recovery/health supervisor.

    Design goal:
    - broad autonomy for reversible/internal work
    - do not add blanket restrictions
    - preserve existing execution/financial controls for irreversible external actions
    - automatic recovery is read-only with respect to blockchain transactions
    """

    def __init__(self, root=None, rpc=None, stale_after_seconds=900):
        self.root = Path(root or Path.home() / "companyos")
        self.runtime = self.root / "companyos_runtime"
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.worker = PendingReconciliationWorker(
            root=self.root,
            rpc=rpc,
            stale_after_seconds=stale_after_seconds,
        )
        self.status_path = self.runtime / "companyos_health_status.json"
        self.heartbeat_path = self.runtime / "companyos_heartbeat.json"
        self.recovery_log = self.runtime / "startup_recovery_history.jsonl"

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    def _write_json(self, path, data):
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")
        os.replace(tmp, path)

    def _append_jsonl(self, path, data):
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(data, sort_keys=True, default=str) + "\n")

    def component_checks(self):
        checks = {}

        # Files/modules required for launch core.
        required = {
            "pending_recovery": self.root / "companyos" / "walletintegration" / "pending_recovery.py",
            "reconciliation_worker": self.root / "companyos" / "walletintegration" / "reconciliation_worker.py",
            "receipt_verifier": self.root / "companyos" / "walletintegration" / "receipt_verifier.py",
            "solana_execution_gate": self.root / "companyos" / "walletintegration" / "solana_execution_gate.py",
            "live_orchestrator": self.root / "companyos" / "liveintegration" / "live_orchestrator.py",
        }

        for name, path in required.items():
            checks[name] = {
                "present": path.exists(),
                "path": str(path),
            }

        checks["runtime_writable"] = {
            "present": self.runtime.exists() and os.access(self.runtime, os.W_OK),
            "path": str(self.runtime),
        }

        return checks

    def evaluate(self):
        components = self.component_checks()
        pending = self.worker.inspect()

        missing = [
            name for name, row in components.items()
            if not row.get("present")
        ]

        # This is deliberately not a blanket autonomy blocker.
        # Internal/reversible automation can continue even with degraded health.
        # External irreversible execution should continue to rely on its existing
        # execution gates, authorization, kill-switch, wallet and policy controls.
        if missing:
            health = "degraded"
        elif pending.get("stale_count", 0) > 0:
            health = "attention"
        else:
            health = "healthy"

        result = {
            "success": True,
            "status": "companyos_health_evaluated",
            "health": health,
            "timestamp": self._now(),
            "components": components,
            "pending": {
                "count": pending.get("pending_count", 0),
                "stale_count": pending.get("stale_count", 0),
            },
            "autonomy_policy": {
                "internal_reversible_actions": "allowed_by_existing_system_logic",
                "research_planning_building_learning": "not_restricted_by_phase68",
                "external_irreversible_actions": "existing_controls_preserved",
                "automatic_transaction_rebroadcast": False,
            },
        }
        self._write_json(self.status_path, result)
        return result

    def startup_recover(self, limit=100):
        before = self.evaluate()
        reconcile = self.worker.run_once(limit=limit)
        after = self.evaluate()

        result = {
            "success": True,
            "status": "startup_recovery_complete",
            "timestamp": self._now(),
            "before": before,
            "reconcile": reconcile,
            "after": after,
            "transaction_created": False,
            "signing_performed": False,
            "broadcast_performed": False,
            "rebroadcast_performed": False,
        }
        self._append_jsonl(self.recovery_log, result)
        return result

    def heartbeat(self):
        status = self.evaluate()
        beat = {
            "success": True,
            "status": "heartbeat",
            "timestamp": self._now(),
            "health": status.get("health"),
            "pending_count": (status.get("pending") or {}).get("count", 0),
            "stale_pending_count": (status.get("pending") or {}).get("stale_count", 0),
        }
        self._write_json(self.heartbeat_path, beat)
        return beat
