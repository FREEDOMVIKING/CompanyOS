from pathlib import Path
import json

from companyos.liveintegration.live_orchestrator import FinalLiveExecutionOrchestrator
from companyos.walletsource.identity_loader import VerifiedWalletIdentity

root = Path.home() / "companyos"

identity = VerifiedWalletIdentity(root).load()
assert identity.get("success") is True, identity

destination = identity.get("public_address")
assert destination, "VERIFIED_SOLANA_ADDRESS_MISSING"

orch = FinalLiveExecutionOrchestrator(root)

assert destination in orch.allowlist, \
    "VERIFIED_DESTINATION_NOT_IN_PERSISTENT_ALLOWLIST"

events = []
captured_receipts = []
captured_locks = []

def readiness():
    events.append("readiness")
    return {
        "success": True,
        "status": "synthetic_readiness_pass",
        "ready_for_controlled_live_review": True,
    }

orch.readiness.evaluate = readiness

def guard(*args, **kwargs):
    events.append("runtime_guard")
    return {
        "success": True,
        "allowed": True,
        "status": "synthetic_runtime_guard_pass",
    }

orch.guard.check = guard

def authorization(*args, **kwargs):
    events.append("authorization")
    return {
        "success": True,
        "allowed": True,
        "status": "synthetic_authorization_pass",
        "dry_run_only": True,
    }

orch.auth.validate = authorization

def prepare(*args, **kwargs):
    events.append("transaction_prepare")
    return {
        "success": True,
        "status": "synthetic_transaction_prepared",
        "source": destination,
        "destination": destination,
        "amount": 0.0001,
        "token": "SYNTHETIC_PHASE55B_TOKEN",
        "chain": "solana",
        "memo": "Phase 55B simulated success path",
        "fingerprint": "PHASE55B_SYNTHETIC_FINGERPRINT",
        "proposal": {
            "source": destination,
            "destination": destination,
            "amount": 0.0001,
            "token": "SYNTHETIC_PHASE55B_TOKEN",
            "chain": "solana",
            "memo": "Phase 55B simulated success path",
        },
    }

orch.tx.prepare = prepare

def execute(*args, **kwargs):
    events.append("execution_gate")
    return {
        "success": True,
        "status": "dry_run_execution_complete",
        "dry_run": True,
        "signed": False,
        "broadcast_attempted": False,
        "transaction_id": None,
        "signature": None,
        "transaction_hash": None,
    }

orch.execgate.prepare_and_execute = execute

def append_receipt(record, *args, **kwargs):
    events.append("receipt")
    captured_receipts.append(record)
    return {
        "success": True,
        "status": "receipt_captured_in_memory",
    }

orch.receipts.append = append_receipt

def engage_lock(*args, **kwargs):
    events.append("post_execution_lock")
    reason = kwargs.get("reason", "controlled_live_attempt_complete")
    captured_locks.append(reason)
    return {
        "success": True,
        "status": "post_execution_lock_simulated",
        "state": {
            "locked": False,
            "reason": reason,
            "in_memory_only": True,
        },
    }

orch.postlock.engage = engage_lock

print("ORCHESTRATOR:", type(orch).__name__)
print("DESTINATION_VERIFIED:", True)
print("ALLOWLIST_MATCH:", destination in orch.allowlist)

result = orch.execute_once(
    token="SYNTHETIC_PHASE55B_TOKEN",
    destination=destination,
    amount=0.0001,
    balance=1000.0,
    estimated_fee=0.00001,
    memo="Phase 55B simulated success path",
)

print("\n===== RESULT =====")
print(json.dumps(result, indent=2, default=str))

print("\n===== EVENT ORDER =====")
print(json.dumps(events, indent=2))

expected_order = [
    "readiness",
    "runtime_guard",
    "authorization",
    "transaction_prepare",
    "execution_gate",
    "receipt",
    "post_execution_lock",
]

assert events == expected_order, (
    f"INVALID_EVENT_ORDER: expected={expected_order}, actual={events}"
)

assert len(captured_receipts) == 1, \
    f"EXPECTED_ONE_RECEIPT_CAPTURE, got {len(captured_receipts)}"

assert len(captured_locks) == 1, \
    f"EXPECTED_ONE_LOCK_CAPTURE, got {len(captured_locks)}"

execution = result.get("execution", {})

assert result.get("success") is True, result
assert execution.get("success") is True, execution
assert execution.get("dry_run") is True, execution
assert execution.get("signed") is False, execution
assert execution.get("broadcast_attempted") is False, execution
assert execution.get("transaction_id") is None, execution
assert execution.get("signature") is None, execution
assert execution.get("transaction_hash") is None, execution

print("\n======================================")
print("PHASE55B_SUCCESS_PATH_RETEST: PASS")
print("======================================")
print("PIPELINE_ORDER_VALID: True")
print("EXECUTION_GATE_REACHED: True")
print("RECEIPT_CAPTURED_IN_MEMORY: True")
print("POSTLOCK_SIMULATED_IN_MEMORY: True")
print("PERSISTENT_STATE_CHANGED: False")
print("REAL_AUTH_CREATED: False")
print("REAL_RECEIPT_WRITTEN: False")
print("REAL_LOCK_ENGAGED: False")
print("TRANSACTION_CREATED: False")
print("TRANSACTION_SIGNED: False")
print("BROADCAST_ATTEMPTED: False")
