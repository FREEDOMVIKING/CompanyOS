from pathlib import Path
import json

from companyos.liveintegration.live_orchestrator import FinalLiveExecutionOrchestrator
from companyos.walletsource.identity_loader import VerifiedWalletIdentity

root = Path.home() / "companyos"

print("===== PHASE 60: IDEMPOTENCY & REPLAY PROTECTION AUDIT =====")

identity = VerifiedWalletIdentity(root).load()
assert identity.get("success") is True, identity

destination = identity.get("public_address")
assert destination, "VERIFIED_PUBLIC_ADDRESS_MISSING"

orch = FinalLiveExecutionOrchestrator(root)

checks = {}

def record(name, passed, detail=None):
    checks[name] = {"passed": bool(passed), "detail": detail}
    print(f"{name}: {bool(passed)}")
    if detail is not None:
        print("  detail:", detail)

record(
    "VERIFIED_DESTINATION_IN_ALLOWLIST",
    destination in orch.allowlist,
    f"allowlist_count={len(orch.allowlist)}",
)

# Locate idempotency component.
idempotency = getattr(orch, "idempotency", None)

if idempotency is None:
    idempotency = getattr(getattr(orch, "execgate", None), "idempotency", None)

record(
    "IDEMPOTENCY_COMPONENT_PRESENT",
    idempotency is not None,
    type(idempotency).__name__ if idempotency else "MISSING",
)

# Inspect likely public methods without mutating persistent state.
method_names = [
    "get",
    "put",
    "check",
    "seen",
    "exists",
    "record",
]

available_methods = {}

if idempotency is not None:
    for name in method_names:
        fn = getattr(idempotency, name, None)
        available_methods[name] = callable(fn)

record(
    "IDEMPOTENCY_PUBLIC_METHOD_FOUND",
    any(available_methods.values()),
    available_methods,
)

# Verify execute_once source contains idempotency/replay logic.
import inspect

try:
    source = inspect.getsource(orch.execute_once)
except Exception:
    source = ""

source_lower = source.lower()

record(
    "EXECUTE_ONCE_REFERENCES_IDEMPOTENCY",
    "idempot" in source_lower,
    "idempot" in source_lower,
)

record(
    "EXECUTE_ONCE_REFERENCES_REPLAY",
    ("replay" in source_lower) or ("prior" in source_lower),
    ("replay" in source_lower) or ("prior" in source_lower),
)

# Check postlock is clear before any future controlled execution.
postlock = orch.postlock.status()

record(
    "POSTLOCK_CLEAR",
    not bool(postlock.get("locked", False)),
    postlock,
)

# Check policy remains fail-closed.
controller = getattr(orch.execgate, "controller", None)
policy = getattr(controller, "policy", None) if controller else None

record(
    "SPEND_CONTROLLER_PRESENT",
    controller is not None,
    type(controller).__name__ if controller else "MISSING",
)

record(
    "TREASURY_POLICY_PRESENT",
    policy is not None,
    type(policy).__name__ if policy else "MISSING",
)

if policy is not None:
    record(
        "AUTONOMOUS_TRANSFERS_DISABLED",
        getattr(policy, "allow_autonomous_transfers", None) is False,
        getattr(policy, "allow_autonomous_transfers", None),
    )

    record(
        "ALLOWLIST_REQUIRED",
        getattr(policy, "require_allowlist", None) is True,
        getattr(policy, "require_allowlist", None),
    )

# Read-only readiness snapshot.
try:
    readiness = orch.readiness.evaluate()
except Exception as exc:
    readiness = {
        "success": False,
        "status": "readiness_snapshot_error",
        "error": f"{type(exc).__name__}: {exc}",
    }

record(
    "READINESS_SNAPSHOT_RETURNED",
    isinstance(readiness, dict),
    readiness.get("status") if isinstance(readiness, dict) else None,
)

failed = [name for name, item in checks.items() if not item["passed"]]

report = {
    "success": not failed,
    "failed_checks": failed,
    "idempotency_type": type(idempotency).__name__ if idempotency else None,
    "available_methods": available_methods,
    "postlock": postlock,
    "readiness": readiness,
}

print("\n===== REPORT =====")
print(json.dumps(report, indent=2, default=str))

print("\n==========================================")
print(
    "PHASE60_IDEMPOTENCY_REPLAY_AUDIT:",
    "PASS" if not failed else "REVIEW_REQUIRED",
)
print("==========================================")
print("IDEMPOTENCY_LAYER_PRESENT:", idempotency is not None)
print("REPLAY_PROTECTION_REFERENCED:", ("replay" in source_lower) or ("prior" in source_lower))
print("ALLOWLIST_PRESERVED:", destination in orch.allowlist)
print("POSTLOCK_CLEAR:", not bool(postlock.get("locked", False)))
print("REAL_AUTH_CREATED: False")
print("TRANSACTION_CREATED: False")
print("TRANSACTION_SIGNED: False")
print("BROADCAST_ATTEMPTED: False")

raise SystemExit(0 if not failed else 2)
