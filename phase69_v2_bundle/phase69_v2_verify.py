#!/usr/bin/env python3
from pathlib import Path
import tempfile
from companyos.runtime.launch_readiness_audit import LaunchReadinessAudit

with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    for rel in [
        "companyos/liveintegration/live_orchestrator.py",
        "companyos/walletintegration/solana_execution_gate.py",
        "companyos/walletintegration/receipt_verifier.py",
        "companyos/walletintegration/pending_recovery.py",
        "companyos/walletintegration/reconciliation_worker.py",
        "companyos/runtime/health_supervisor.py",
    ]:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# mock\n", encoding="utf-8")

    audit = LaunchReadinessAudit(root=root)
    result = audit.run()

    checks = {
        "audit_success": result.get("success") is True,
        "report_written": audit.report_path.exists(),
        "blanket_restrictions_false": result["autonomy_policy"]["blanket_restrictions_added"] is False,
        "secrets_not_exposed": all("value" not in k.lower() for k in result.get("credential_presence", {})),
    }

    ok = all(checks.values())
    for k, v in checks.items():
        print(k, "=>", "PASS" if v else "FAIL")
    print("PHASE69_V2_VERIFY:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
