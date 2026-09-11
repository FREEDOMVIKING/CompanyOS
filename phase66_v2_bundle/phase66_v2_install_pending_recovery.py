#!/usr/bin/env python3
from __future__ import annotations
import ast, datetime as dt, json, py_compile, shutil
from pathlib import Path

ROOT = Path.home() / "companyos"
PKG = ROOT / "companyos"
WALLET = PKG / "walletintegration"
LIVE = PKG / "liveintegration"
RECOVERY = WALLET / "pending_recovery.py"
GATE = WALLET / "solana_execution_gate.py"
ORCH = LIVE / "live_orchestrator.py"
MANIFEST = ROOT / "PHASE66_V2_INSTALLED.json"

SOURCE = (Path(__file__).with_name("pending_recovery.py")).read_text(encoding="utf-8")

def backup(path, stamp):
    if not path.exists():
        return None
    dst = path.with_name(path.name + f".phase66_v2_backup_{stamp}")
    shutil.copy2(path, dst)
    return str(dst)

def main():
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    WALLET.mkdir(parents=True, exist_ok=True)
    backups = {
        "pending_recovery": backup(RECOVERY, stamp),
        "solana_execution_gate": backup(GATE, stamp),
        "live_orchestrator": backup(ORCH, stamp),
    }

    ast.parse(SOURCE)
    RECOVERY.write_text(SOURCE, encoding="utf-8")

    gate_patched = False
    orch_patched = False

    if GATE.exists():
        s = GATE.read_text(encoding="utf-8")
        if "Phase 66 V2 pending recovery hook" not in s:
            import_line = "from companyos.walletintegration.pending_recovery import PendingTransactionRecovery\n"
            if import_line not in s:
                lines = s.splitlines(True)
                idx = 0
                for i, line in enumerate(lines):
                    if line.startswith("from ") or line.startswith("import "):
                        idx = i + 1
                    elif idx and line.strip():
                        break
                lines.insert(idx, import_line)
                s = "".join(lines)

            if "self.pending_recovery = PendingTransactionRecovery(root)" not in s:
                for needle in [
                    "        self.verifier = OnChainReceiptVerifier()\n",
                    "        self.adapter = self._load_adapter()\n",
                ]:
                    if needle in s:
                        s = s.replace(
                            needle,
                            needle + "        self.pending_recovery = PendingTransactionRecovery(root)\n",
                            1,
                        )
                        break

            hook_point = "    self.idempotency.put(idempotency_key, out)\n"
            if hook_point in s and '"tx_id": verification.get("tx_id")' in s:
                hook = '''    # Phase 66 V2 pending recovery hook: persistence only, never rebroadcast.
    if out.get("status") == "execution_pending_confirmation" and out.get("tx_id"):
        out["pending_recovery"] = self.pending_recovery.register(
            out.get("tx_id"),
            destination=destination,
            amount=float(amount),
            source=source,
            execution_status=out.get("status"),
            receipt_id=(receipt or {}).get("receipt_id") if isinstance(receipt, dict) else None,
            metadata={"idempotency_key": idempotency_key},
        )

'''
                s = s.replace(hook_point, hook + hook_point, 1)
                ast.parse(s)
                GATE.write_text(s, encoding="utf-8")
                gate_patched = True

    if ORCH.exists():
        s = ORCH.read_text(encoding="utf-8")
        needle = '            "verification":result.get("verification"),\n'
        add = '            "pending_recovery":result.get("pending_recovery"),\n'
        if add not in s and needle in s:
            s = s.replace(needle, needle + add, 1)
            ast.parse(s)
            ORCH.write_text(s, encoding="utf-8")
            orch_patched = True

    py_compile.compile(str(RECOVERY), doraise=True)
    if GATE.exists():
        py_compile.compile(str(GATE), doraise=True)
    if ORCH.exists():
        py_compile.compile(str(ORCH), doraise=True)

    manifest = {
        "phase": "66_V2",
        "status": "installed",
        "installed_at_utc": stamp,
        "backups": backups,
        "gate_pending_hook_installed": gate_patched,
        "orchestrator_receipt_hook_installed": orch_patched,
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
    print("GATE_PENDING_HOOK_INSTALLED:", gate_patched)
    print("ORCHESTRATOR_RECEIPT_HOOK_INSTALLED:", orch_patched)
    print("NO_TRANSACTION_CREATED_BY_INSTALLER: True")
    print("NO_SIGNING_PERFORMED_BY_INSTALLER: True")
    print("NO_BROADCAST_PERFORMED_BY_INSTALLER: True")
    print("RECOVERY_REBROADCASTS: False")
    print("MANIFEST:", MANIFEST)

if __name__ == "__main__":
    main()
