from pathlib import Path
from tempfile import TemporaryDirectory
import json

from companyos.liveintegration.live_orchestrator import FinalLiveExecutionOrchestrator
from companyos.controlledexec.postlock import PostExecutionLock
from companyos.walletsource.identity_loader import VerifiedWalletIdentity

root = Path.home() / "companyos"

print("===== PHASE 63C V2: ORCHESTRATOR LOCK FAIL-CLOSED TEST =====")

identity = VerifiedWalletIdentity(root).load()
assert identity.get("success") is True, identity

destination = identity.get("public_address")
assert destination, "VERIFIED_PUBLIC_ADDRESS_MISSING"

orch = FinalLiveExecutionOrchestrator(root)

assert destination in orch.allowlist, \
    "VERIFIED_DESTINATION_NOT_IN_ALLOWLIST"

events = []

with TemporaryDirectory(prefix="companyos_phase63c_v2_") as td:
    isolated_lock = PostExecutionLock(Path(td))
    orch.postlock = isolated_lock

    engage = orch.postlock.engage("phase63c_v2_preexisting_lock")
    assert engage.get("success") is True, engage
    assert orch.postlock.status().get("locked") is True

    # These stubs are safe and complete enough to satisfy the real
    # orchestrator contract if it incorrectly proceeds past the lock.
    def readiness(*args, **kwargs):
        events.append("readiness")
        return {
            "success": True,
            "status": "synthetic_readiness_pass",
            "ready_for_controlled_live_review": True,
        }

    def guard(*args, **kwargs):
        events.append("runtime_guard")
        return {
            "success": True,
            "allowed": True,
            "status": "synthetic_runtime_guard_pass",
        }

    def auth_validate(*args, **kwargs):
        events.append("authorization")
        return {
            "success": True,
            "allowed": True,
            "status": "synthetic_authorization_pass",
            "dry_run_only": True,
        }

    def prepare(*args, **kwargs):
        events.append("transaction_prepare")
        return {
            "success": True,
            "status": "synthetic_transaction_prepared",
            "fingerprint": "PHASE63C_V2_SYNTHETIC_FINGERPRINT",
            "proposal": {
                "source": destination,
                "destination": destination,
                "amount": 0.0001,
                "token": "SYNTHETIC_PHASE63C_V2_TOKEN",
                "chain": "solana",
                "memo": "Phase 63C V2 lock fail-closed test",
            },
        }

    def execute(*args, **kwargs):
        events.append("execution_gate")
        return {
            "success": False,
            "status": "ERROR_EXECUTION_GATE_REACHED",
            "dry_run": True,
            "signed": False,
            "broadcast_attempted": False,
            "transaction_id": None,
            "signature": None,
            "transaction_hash": None,
        }

    def receipt(*args, **kwargs):
        events.append("receipt")
        return {
            "success": True,
            "status": "receipt_captured_in_memory",
        }

    orch.readiness.evaluate = readiness
    orch.guard.check = guard
    orch.auth.validate = auth_validate
    orch.tx.prepare = prepare
    orch.execgate.prepare_and_execute = execute
    orch.receipts.append = receipt

    result = orch.execute_once(
        token="SYNTHETIC_PHASE63C_V2_TOKEN",
        destination=destination,
        amount=0.0001,
        balance=1000.0,
        estimated_fee=0.00001,
        memo="Phase 63C V2 preexisting lock fail-closed test",
    )

    print("\n===== RESULT =====")
    print(json.dumps(result, indent=2, default=str))

    print("\n===== EVENTS =====")
    print(json.dumps(events, indent=2))

    result_text = json.dumps(result, default=str).lower()
    status_text = str(result.get("status", "")).lower()

    lock_block_detected = (
        "post_execution_lock_active" in result_text
        or "lock" in status_text
        or "locked" in result_text
    )

    assert lock_block_detected, \
        f"LOCK_BLOCK_NOT_DETECTED: {result}"

    assert "execution_gate" not in events, \
        f"EXECUTION_GATE_REACHED_DESPITE_PREEXISTING_LOCK: {events}"

    assert "receipt" not in events, \
        f"RECEIPT_WRITTEN_DESPITE_PREEXISTING_LOCK: {events}"

    assert '"signed": true' not in result_text, \
        "UNEXPECTED_SIGNING_DETECTED"

    assert '"broadcast_attempted": true' not in result_text, \
        "UNEXPECTED_BROADCAST_DETECTED"

    final_isolated_state = orch.postlock.status()

    assert final_isolated_state.get("locked") is True, \
        final_isolated_state

print("\n==============================================")
print("PHASE63C_V2_ORCHESTRATOR_LOCK_FAIL_CLOSED: PASS")
print("==============================================")
print("PREEXISTING_LOCK_RECOGNIZED: True")
print("EXECUTION_GATE_REACHED:", "execution_gate" in events)
print("RECEIPT_REACHED:", "receipt" in events)
print("TRANSACTION_SIGNED: False")
print("BROADCAST_ATTEMPTED: False")
print("REAL_COMPANYOS_LOCK_TOUCHED: False")
