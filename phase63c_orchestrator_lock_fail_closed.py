from pathlib import Path
from tempfile import TemporaryDirectory
import json

from companyos.liveintegration.live_orchestrator import FinalLiveExecutionOrchestrator
from companyos.controlledexec.postlock import PostExecutionLock
from companyos.walletsource.identity_loader import VerifiedWalletIdentity

root = Path.home() / "companyos"

print("===== PHASE 63C: ORCHESTRATOR LOCK FAIL-CLOSED TEST =====")

identity = VerifiedWalletIdentity(root).load()
assert identity.get("success") is True, identity

destination = identity.get("public_address")
assert destination, "VERIFIED_PUBLIC_ADDRESS_MISSING"

# Real orchestrator object, but no real execution path will be allowed.
orch = FinalLiveExecutionOrchestrator(root)

assert destination in orch.allowlist, \
    "VERIFIED_DESTINATION_NOT_IN_ALLOWLIST"

events = []

# Replace the real postlock component with an isolated temporary lock
# so the real CompanyOS lock file is never touched.
with TemporaryDirectory(prefix="companyos_phase63c_") as td:
    isolated_lock = PostExecutionLock(Path(td))
    orch.postlock = isolated_lock

    # Engage the isolated lock before execute_once().
    engage = orch.postlock.engage("phase63c_preexisting_lock")
    assert engage.get("success") is True, engage
    assert orch.postlock.status().get("locked") is True

    # Any stage after lock recognition is dangerous for this test.
    # Mark them so we can prove they were not reached.
    def forbidden_readiness(*args, **kwargs):
        events.append("readiness")
        return {
            "success": True,
            "status": "unexpected_readiness_reached",
            "ready_for_controlled_live_review": True,
        }

    def forbidden_guard(*args, **kwargs):
        events.append("runtime_guard")
        return {
            "success": True,
            "allowed": True,
            "status": "unexpected_guard_reached",
        }

    def forbidden_auth(*args, **kwargs):
        events.append("authorization")
        return {
            "success": True,
            "allowed": True,
            "status": "unexpected_auth_reached",
        }

    def forbidden_prepare(*args, **kwargs):
        events.append("transaction_prepare")
        return {
            "success": True,
            "status": "unexpected_prepare_reached",
            "source": destination,
            "fingerprint": "PHASE63C_SHOULD_NOT_EXIST",
        }

    def forbidden_execute(*args, **kwargs):
        events.append("execution_gate")
        return {
            "success": False,
            "status": "ERROR_EXECUTION_GATE_REACHED",
            "signed": False,
            "broadcast_attempted": False,
        }

    orch.readiness.evaluate = forbidden_readiness
    orch.guard.check = forbidden_guard
    orch.auth.validate = forbidden_auth
    orch.tx.prepare = forbidden_prepare
    orch.execgate.prepare_and_execute = forbidden_execute

    result = orch.execute_once(
        token="SYNTHETIC_PHASE63C_TOKEN",
        destination=destination,
        amount=0.0001,
        balance=1000.0,
        estimated_fee=0.00001,
        memo="Phase 63C preexisting lock fail-closed test",
    )

    print("\n===== RESULT =====")
    print(json.dumps(result, indent=2, default=str))

    print("\n===== EVENTS =====")
    print(json.dumps(events, indent=2))

    status_text = str(result.get("status", "")).lower()
    result_text = json.dumps(result, default=str).lower()

    blocked_by_lock = (
        "lock" in status_text
        or "post_execution_lock" in result_text
        or "locked" in result_text
    )

    assert blocked_by_lock, \
        f"RESULT_DID_NOT_INDICATE_LOCK_BLOCK: {result}"

    assert "execution_gate" not in events, \
        f"EXECUTION_GATE_REACHED_DESPITE_LOCK: {events}"

    assert '"signed": true' not in result_text, \
        "UNEXPECTED_SIGNING_DETECTED"

    assert '"broadcast_attempted": true' not in result_text, \
        "UNEXPECTED_BROADCAST_DETECTED"

    isolated_state = orch.postlock.status()
    assert isolated_state.get("locked") is True, isolated_state

print("\n==========================================")
print("PHASE63C_ORCHESTRATOR_LOCK_FAIL_CLOSED: PASS")
print("==========================================")
print("PREEXISTING_LOCK_RECOGNIZED: True")
print("EXECUTION_GATE_REACHED:", "execution_gate" in events)
print("TRANSACTION_SIGNED: False")
print("BROADCAST_ATTEMPTED: False")
print("REAL_COMPANYOS_LOCK_TOUCHED: False")
