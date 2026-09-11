from pathlib import Path
import inspect
import json

from companyos.liveintegration.live_orchestrator import FinalLiveExecutionOrchestrator
from companyos.walletsource.identity_loader import VerifiedWalletIdentity

root = Path.home() / "companyos"

print("===== PHASE 63: POST-EXECUTION LOCK & RECOVERY AUDIT =====")

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

postlock = getattr(orch, "postlock", None)

record(
    "POSTLOCK_COMPONENT_PRESENT",
    postlock is not None,
    type(postlock).__name__ if postlock else "MISSING",
)

methods = {}
signatures = {}

if postlock is not None:
    for name in ["engage", "clear", "status"]:
        fn = getattr(postlock, name, None)
        methods[name] = callable(fn)
        if callable(fn):
            try:
                signatures[name] = str(inspect.signature(fn))
            except Exception:
                signatures[name] = "<signature unavailable>"

for name in ["engage", "clear", "status"]:
    record(
        f"POSTLOCK_{name.upper()}_PRESENT",
        methods.get(name, False),
        signatures.get(name),
    )

# Inspect source for persistent lock semantics without modifying state.
source = ""
if postlock is not None:
    try:
        source = inspect.getsource(type(postlock))
    except Exception:
        source = ""

lower = source.lower()

record(
    "POSTLOCK_SOURCE_HAS_LOCKED_STATE",
    "locked" in lower,
    "locked" in lower,
)

record(
    "POSTLOCK_SOURCE_HAS_REASON_STATE",
    "reason" in lower,
    "reason" in lower,
)

record(
    "POSTLOCK_SOURCE_HAS_TIMESTAMP_STATE",
    any(x in lower for x in ["timestamp", "locked_at", "time"]),
    [x for x in ["timestamp", "locked_at", "time"] if x in lower],
)

# Verify execute_once engages lock after an execution attempt.
try:
    execute_source = inspect.getsource(orch.execute_once)
except Exception:
    execute_source = ""

exec_lower = execute_source.lower()

record(
    "EXECUTE_ONCE_REFERENCES_POSTLOCK",
    "postlock" in exec_lower,
    "postlock" in exec_lower,
)

record(
    "EXECUTE_ONCE_REFERENCES_LOCK_ENGAGE",
    "engage" in exec_lower,
    "engage" in exec_lower,
)

# Current state must be readable and clear.
state = postlock.status() if postlock is not None else {}

record(
    "POSTLOCK_STATUS_READABLE",
    isinstance(state, dict),
    state,
)

record(
    "POSTLOCK_CURRENTLY_CLEAR",
    not bool(state.get("locked", False)),
    state.get("locked"),
)

# Verify persistent allowlist and fail-closed policy remain intact.
record(
    "VERIFIED_DESTINATION_IN_ALLOWLIST",
    destination in orch.allowlist,
    f"allowlist_count={len(orch.allowlist)}",
)

controller = getattr(orch.execgate, "controller", None)
policy = getattr(controller, "policy", None) if controller else None

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
    "postlock_type": type(postlock).__name__ if postlock else None,
    "methods": methods,
    "signatures": signatures,
    "state": state,
    "readiness": readiness,
}

print("\n===== REPORT =====")
print(json.dumps(report, indent=2, default=str))

print("\n==========================================")
print(
    "PHASE63_POSTLOCK_RECOVERY_AUDIT:",
    "PASS" if not failed else "REVIEW_REQUIRED",
)
print("==========================================")
print("POSTLOCK_LAYER_PRESENT:", postlock is not None)
print("LOCK_ENGAGE_PRESENT:", methods.get("engage", False))
print("LOCK_CLEAR_PRESENT:", methods.get("clear", False))
print("LOCK_STATUS_PRESENT:", methods.get("status", False))
print("POSTLOCK_CLEAR:", not bool(state.get("locked", False)))
print("ALLOWLIST_PRESERVED:", destination in orch.allowlist)
print("REAL_AUTH_CREATED: False")
print("TRANSACTION_CREATED: False")
print("TRANSACTION_SIGNED: False")
print("BROADCAST_ATTEMPTED: False")

raise SystemExit(0 if not failed else 2)
