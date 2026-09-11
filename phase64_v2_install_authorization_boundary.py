#!/usr/bin/env python3
from __future__ import annotations

import ast
import datetime as _dt
import json
import py_compile
import shutil
from pathlib import Path

ROOT = Path.home() / "companyos"
TARGET = ROOT / "companyos" / "liveintegration" / "live_orchestrator.py"
MANIFEST = ROOT / "PHASE64_V2_INSTALLED.json"

OLD = '''        # The existing Solana gate owns signing + provider-specific execution.
        execution_gate_reached = False

        result=self.execgate.prepare_and_execute(
            amount=amount,
            balance=balance,
            destination=destination,
            source=prepared["proposal"]["source"],
            memo=memo,
            idempotency_key=prepared["fingerprint"],
            dry_run=False,
            signing_authorized=True
        )

        execution_gate_reached = True

        # One-shot auth is consumed only after the execution gate was reached.
        self.auth.consume()
'''

NEW = '''        # Phase 64 V2: consume the one-shot authorization BEFORE crossing
        # the live execution boundary. A valid authorization becomes single-use
        # before downstream execution is attempted.
        auth_consume = self.auth.consume()
        if not auth_consume.get("success"):
            return {
                "success": False,
                "status": auth_consume.get("status", "authorization_consume_failed"),
                "authorization": auth,
                "authorization_consumed": False,
            }

        # The existing Solana gate owns signing + provider-specific execution.
        execution_gate_reached = False

        result=self.execgate.prepare_and_execute(
            amount=amount,
            balance=balance,
            destination=destination,
            source=prepared["proposal"]["source"],
            memo=memo,
            idempotency_key=prepared["fingerprint"],
            dry_run=False,
            signing_authorized=True
        )

        execution_gate_reached = True
'''

def main() -> int:
    if not TARGET.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")

    if "Phase 63D V2: fail closed on pre-existing post-execution lock." not in src:
        raise SystemExit("REFUSED: Phase 63D V2 guard marker not found.")

    if "Phase 64 V2: consume the one-shot authorization BEFORE crossing" in src:
        print("PHASE64_V2_AUTHORIZATION_BOUNDARY: ALREADY_INSTALLED")
        py_compile.compile(str(TARGET), doraise=True)
        print("COMPILE_CHECK: PASS")
        return 0

    if OLD not in src:
        raise SystemExit("REFUSED: expected execution/auth block not found exactly; no changes were made.")

    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = TARGET.with_name(f"{TARGET.name}.phase64_v2_backup_{stamp}")
    shutil.copy2(TARGET, backup)

    patched = src.replace(OLD, NEW, 1)

    ast.parse(patched)

    guard_pos = patched.find("postlock_state = self.postlock.status()")
    auth_pos = patched.find("auth=self.auth.validate(token, amount, destination)")
    consume_pos = patched.find("auth_consume = self.auth.consume()")
    gate_pos = patched.find("result=self.execgate.prepare_and_execute(")

    if min(guard_pos, auth_pos, consume_pos, gate_pos) < 0:
        raise SystemExit("INVARIANT_FAILED: required source markers missing.")
    if not (guard_pos < auth_pos < consume_pos < gate_pos):
        raise SystemExit("INVARIANT_FAILED: execution-control ordering is not fail-closed.")

    TARGET.write_text(patched, encoding="utf-8")

    try:
        py_compile.compile(str(TARGET), doraise=True)
    except Exception:
        shutil.copy2(backup, TARGET)
        raise

    manifest = {
        "phase": "64_V2",
        "status": "installed",
        "target": str(TARGET),
        "backup": str(backup),
        "invariants": {
            "phase63d_guard_preserved_before_auth": True,
            "authorization_consumed_before_execution_gate": True,
            "consume_failure_fails_closed": True,
            "installer_creates_no_transaction": True,
            "installer_performs_no_signing": True,
            "installer_performs_no_broadcast": True
        },
        "installed_at_utc": stamp
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print("PHASE64_V2_AUTHORIZATION_BOUNDARY: INSTALLED")
    print("COMPILE_CHECK: PASS")
    print("PHASE63D_GUARD_PRESERVED: True")
    print("AUTH_CONSUMED_BEFORE_EXECUTION_GATE: True")
    print("CONSUME_FAILURE_FAILS_CLOSED: True")
    print("NO_TRANSACTION_CREATED_BY_INSTALLER: True")
    print("NO_SIGNING_PERFORMED_BY_INSTALLER: True")
    print("NO_BROADCAST_PERFORMED_BY_INSTALLER: True")
    print(f"BACKUP: {backup}")
    print(f"MANIFEST: {MANIFEST}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
