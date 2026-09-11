from __future__ import annotations

import importlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


class LaunchReadinessAudit:
    """
    Phase 69 V2 launch-readiness audit.

    Philosophy:
    - Do not globally restrict CompanyOS autonomy.
    - Audit and report readiness.
    - Existing execution/financial controls remain the source of truth.
    - Missing optional capabilities are warnings, not blanket blockers.
    """

    def __init__(self, root=None):
        self.root = Path(root or Path.home() / "companyos")
        self.runtime = self.root / "companyos_runtime"
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.report_path = self.runtime / "launch_readiness_audit.json"

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    def _exists(self, rel):
        return (self.root / rel).exists()

    def _env_present(self, name):
        return bool(os.getenv(name, "").strip())

    def run(self):
        required_files = {
            "live_orchestrator": self._exists("companyos/liveintegration/live_orchestrator.py"),
            "solana_execution_gate": self._exists("companyos/walletintegration/solana_execution_gate.py"),
            "receipt_verifier": self._exists("companyos/walletintegration/receipt_verifier.py"),
            "pending_recovery": self._exists("companyos/walletintegration/pending_recovery.py"),
            "reconciliation_worker": self._exists("companyos/walletintegration/reconciliation_worker.py"),
            "health_supervisor": self._exists("companyos/runtime/health_supervisor.py"),
        }

        import_checks = {}
        for mod in [
            "companyos.walletintegration.pending_recovery",
            "companyos.walletintegration.reconciliation_worker",
            "companyos.walletintegration.receipt_verifier",
            "companyos.runtime.health_supervisor",
        ]:
            try:
                importlib.import_module(mod)
                import_checks[mod] = True
            except Exception as exc:
                import_checks[mod] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

        env = {
            "SOLANA_RPC_URL": self._env_present("SOLANA_RPC_URL"),
            "COMPANYOS_ENABLE_LIVE_FINANCIAL_EXECUTION": self._env_present(
                "COMPANYOS_ENABLE_LIVE_FINANCIAL_EXECUTION"
            ),
        }

        # Credentials are intentionally reported only as present/absent.
        # Never print secret values.
        credential_presence = {
            "SOLANA_PRIVATE_KEY_present": self._env_present("SOLANA_PRIVATE_KEY"),
            "EVM_PRIVATE_KEY_present": self._env_present("EVM_PRIVATE_KEY"),
            "SMTP_credentials_present": any(
                self._env_present(x)
                for x in ("SMTP_PASSWORD", "SMTP_USERNAME", "SMTP_HOST")
            ),
        }

        core_ok = all(required_files.values()) and all(v is True for v in import_checks.values())

        warnings = []
        if not env["SOLANA_RPC_URL"]:
            warnings.append("SOLANA_RPC_URL not set; live Solana RPC operations may be unavailable.")
        if not credential_presence["SOLANA_PRIVATE_KEY_present"]:
            warnings.append("SOLANA_PRIVATE_KEY not present; Solana signing will be unavailable.")
        if not env["COMPANYOS_ENABLE_LIVE_FINANCIAL_EXECUTION"]:
            warnings.append("Live financial execution flag not set/enabled in environment.")

        report = {
            "success": True,
            "status": "launch_readiness_audit_complete",
            "timestamp": self._now(),
            "core_runtime_ready": core_ok,
            "required_files": required_files,
            "imports": import_checks,
            "environment_presence": env,
            "credential_presence": credential_presence,
            "warnings": warnings,
            "autonomy_policy": {
                "blanket_restrictions_added": False,
                "internal_reversible_autonomy_preserved": True,
                "missing_optional_capability_is_global_blocker": False,
                "existing_execution_controls_preserved": True,
            },
        }

        self.report_path.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
        return report
