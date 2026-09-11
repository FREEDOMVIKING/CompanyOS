#!/usr/bin/env python3
from __future__ import annotations

import ast
import datetime as dt
import json
import py_compile
import shutil
from pathlib import Path

ROOT = Path.home() / "companyos"
PKG = ROOT / "companyos"
WALLET = PKG / "walletintegration"
LIVE = PKG / "liveintegration"

RECOVERY = WALLET / "pending_recovery.py"
GATE = WALLET / "solana_execution_gate.py"
ORCH = LIVE / "live_orchestrator.py"
MANIFEST = ROOT / "PHASE66_V2_INSTALLED.json"

BUNDLE_RECOVERY = ROOT / "pending_recovery.py"

def backup(path: Path, stamp: str):
    if not path.exists():
        return None
    dst = path.with_name(path.name + f".phase66_v2_backup_{stamp}")
    shutil.copy2(path, dst)
    return str(dst)

def install_recovery():
    if not BUNDLE_RECOVERY.exists():
        raise SystemExit("INSTALL_ABORTED: ~/companyos/pending_recovery.py not found")
    source = BUNDLE_RECOVERY.read_text(encoding="utf-8")
    ast.parse(source)
    WALLET.mkdir(parents=True, exist_ok=True)
    RECOVERY.write_text(source, encoding="utf-8")

def patch_gate():
    if not GATE.exists():
        return False, "gate_missing"

    s = GATE.read_text(encoding="utf-8")

    if "Phase 66 V2 pending recovery hook" in s:
        return False, "already_installed"

    import_line = "from companyos.walletintegration.pending_recovery import PendingTransactionRecovery\n"
    if import_line not in s:
        lines = s.splitlines(True)
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith("from ") or line.startswith("import "):
                insert_at = i + 1
            elif insert_at and line.strip():
                break
        lines.insert(insert_at, import_line)
        s = "".join(lines)

    init_line = "        self.pending_recovery = PendingTransactionRecovery(root)\n"
    if init_line not in s:
        inserted = False
        for needle in (
            "        self.verifier = OnChainReceiptVerifier()\n",
            "        self.adapter = self._load_adapter()\n",
        ):
            if needle in s:
                s = s.replace(needle, needle + init_line, 1)
                inserted = True
                break
        if not inserted:
            return False, "safe_init_marker_not_found"

    target = "self.idempotency.put(idempotency_key, out)"
    target_pos = s.find(target)
    if target_pos == -1:
        return False, "idempotency_marker_not_found"

    if '"tx_id": verification.get("tx_id")' not in s:
        return False, "phase65_tx_id_marker_not_found"

    line_start = s.rfind("\n", 0, target_pos) + 1
    indent = s[line_start:target_pos]

    hook = (
        indent + "# Phase 66 V2 pending recovery hook: persistence only, never rebroadcast.\n"
        + indent + 'if out.get("status") == "execution_pending_confirmation" and out.get("tx_id"):\n'
        + indent + '    out["pending_recovery"] = self.pending_recovery.register(\n'
        + indent + '        out.get("tx_id"),\n'
        + indent + '        destination=destination,\n'
        + indent + '        amount=float(amount),\n'
        + indent + '        source=source,\n'
        + indent + '        execution_status=out.get("status"),\n'
        + indent + '        receipt_id=(receipt or {}).get("receipt_id") if isinstance(receipt, dict) else None,\n'
        + indent + '        metadata={"idempotency_key": idempotency_key},\n'
        + indent + '    )\n\n'
    )

    s = s[:line_start] + hook + s[line_start:]
    ast.parse(s)
    GATE.write_text(s, encoding="utf-8")
    return True, "installed"

def patch_orchestrator():
    if not ORCH.exists():
        return False, "orchestrator_missing"

    s = ORCH.read_text(encoding="utf-8")
    add = '            "pending_recovery":result.get("pending_recovery"),\n'
    if add in s:
        return False, "already_installed"

    needle = '            "verification":result.get("verification"),\n'
    if needle not in s:
        return False, "safe_receipt_marker_not_found"

    s = s.replace(needle, needle + add, 1)
    ast.parse(s)
    ORCH.write_text(s, encoding="utf-8")
    return True, "installed"

def restore(path: Path, backup_path):
    if backup_path:
        shutil.copy2(backup_path, path)

def main():
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backups = {
        "pending_recovery": backup(RECOVERY, stamp),
        "solana_execution_gate": backup(GATE, stamp),
        "live_orchestrator": backup(ORCH, stamp),
    }

    try:
        install_recovery()
        gate_changed, gate_status = patch_gate()
        orch_changed, orch_status = patch_orchestrator()

        py_compile.compile(str(RECOVERY), doraise=True)
        if GATE.exists():
            py_compile.compile(str(GATE), doraise=True)
        if ORCH.exists():
            py_compile.compile(str(ORCH), doraise=True)

    except Exception:
        restore(RECOVERY, backups["pending_recovery"])
        restore(GATE, backups["solana_execution_gate"])
        restore(ORCH, backups["live_orchestrator"])
        raise

    manifest = {
        "phase": "66_V2",
        "status": "installed",
        "installed_at_utc": stamp,
        "backups": backups,
        "gate": {"changed": gate_changed, "status": gate_status},
        "orchestrator": {"changed": orch_changed, "status": orch_status},
        "safety": {
            "installer_creates_transaction": False,
            "installer_signs": False,
            "installer_broadcasts": False,
            "recovery_rebroadcasts": False,
            "rpc_checks_read_only": True,
        },
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print("PHASE66_V2_PENDING_RECOVERY: INSTALLED")
    print("COMPILE_CHECK: PASS")
    print("GATE_PENDING_HOOK:", gate_status)
    print("ORCHESTRATOR_RECEIPT_HOOK:", orch_status)
    print("NO_TRANSACTION_CREATED_BY_INSTALLER: True")
    print("NO_SIGNING_PERFORMED_BY_INSTALLER: True")
    print("NO_BROADCAST_PERFORMED_BY_INSTALLER: True")
    print("RECOVERY_REBROADCASTS: False")
    print("MANIFEST:", MANIFEST)

if __name__ == "__main__":
    main()
