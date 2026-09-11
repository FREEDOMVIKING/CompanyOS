#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import py_compile
from pathlib import Path

ROOT = Path.home() / "companyos"
TARGET = ROOT / "companyos" / "liveintegration" / "live_orchestrator.py"

def main() -> int:
    if not TARGET.exists():
        print("PHASE64_V2_VERIFY: FAIL")
        print(f"TARGET_NOT_FOUND: {TARGET}")
        return 1

    src = TARGET.read_text(encoding="utf-8")
    ast.parse(src)
    py_compile.compile(str(TARGET), doraise=True)

    markers = {
        "phase63d_guard_present":
            "Phase 63D V2: fail closed on pre-existing post-execution lock." in src,
        "phase64_v2_marker_present":
            "Phase 64 V2: consume the one-shot authorization BEFORE crossing" in src,
        "consume_call_present":
            "auth_consume = self.auth.consume()" in src,
        "consume_failure_fail_closed":
            '"authorization_consumed": False' in src and
            '"authorization_consume_failed"' in src
    }

    guard_pos = src.find("postlock_state = self.postlock.status()")
    auth_pos = src.find("auth=self.auth.validate(token, amount, destination)")
    consume_pos = src.find("auth_consume = self.auth.consume()")
    gate_pos = src.find("result=self.execgate.prepare_and_execute(")

    ordering = {
        "guard_before_auth_validate":
            min(guard_pos, auth_pos) >= 0 and guard_pos < auth_pos,
        "auth_consumed_before_execution_gate":
            min(consume_pos, gate_pos) >= 0 and consume_pos < gate_pos
    }

    ok = all(markers.values()) and all(ordering.values())

    print("===== PHASE 64 V2 VERIFY =====")
    print(json.dumps({"markers": markers, "ordering": ordering}, indent=2))
    print("COMPILE_CHECK: PASS")
    print(f"PHASE64_V2_VERIFY: {'PASS' if ok else 'FAIL'}")
    print("EXECUTION_GATE_CALLED_BY_VERIFIER: False")
    print("TRANSACTION_CREATED_BY_VERIFIER: False")
    print("SIGNING_PERFORMED_BY_VERIFIER: False")
    print("BROADCAST_PERFORMED_BY_VERIFIER: False")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
