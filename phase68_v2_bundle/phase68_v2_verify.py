#!/usr/bin/env python3
from __future__ import annotations

import tempfile
from pathlib import Path

from companyos.runtime.health_supervisor import CompanyOSHealthSupervisor


class FakeRpc:
    def signature_status(self, signature):
        return {"success": True, "result": {"value": [None]}}


with tempfile.TemporaryDirectory() as td:
    root = Path(td)

    # Build minimal expected file tree for component checks.
    for rel in [
        "companyos/walletintegration/pending_recovery.py",
        "companyos/walletintegration/reconciliation_worker.py",
        "companyos/walletintegration/receipt_verifier.py",
        "companyos/walletintegration/solana_execution_gate.py",
        "companyos/liveintegration/live_orchestrator.py",
    ]:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# test\n", encoding="utf-8")

    sup = CompanyOSHealthSupervisor(root=root, rpc=FakeRpc(), stale_after_seconds=0)
    health = sup.evaluate()
    hb = sup.heartbeat()
    recovery = sup.startup_recover(limit=10)

    checks = {
        "health_success": health.get("success") is True,
        "health_not_blanket_blocked": health.get("autonomy_policy", {}).get(
            "internal_reversible_actions"
        ) == "allowed_by_existing_system_logic",
        "heartbeat_written": sup.heartbeat_path.exists(),
        "status_written": sup.status_path.exists(),
        "startup_recovery_success": recovery.get("success") is True,
        "no_transaction_created": recovery.get("transaction_created") is False,
        "no_signing": recovery.get("signing_performed") is False,
        "no_broadcast": recovery.get("broadcast_performed") is False,
        "no_rebroadcast": recovery.get("rebroadcast_performed") is False,
    }

    ok = all(checks.values())
    for k, v in checks.items():
        print(k, "=>", "PASS" if v else "FAIL")

    print("PHASE68_V2_VERIFY:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
