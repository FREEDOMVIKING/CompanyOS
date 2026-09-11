from pathlib import Path
import json
import inspect

from companyos.liveintegration.live_orchestrator import FinalLiveExecutionOrchestrator
from companyos.walletsource.identity_loader import VerifiedWalletIdentity

root = Path.home() / "companyos"

print("===== PHASE 61: AUTHORIZATION LIFECYCLE & EXPIRY AUDIT =====")

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

auth = getattr(orch, "auth", None)

record(
    "AUTH_COMPONENT_PRESENT",
    auth is not None,
    type(auth).__name__ if auth else "MISSING",
)

# Capture public authorization methods.
candidate_methods = [
    "create",
    "validate",
    "consume",
    "status",
    "clear",
]

available = {}
signatures = {}

if auth is not None:
    for name in candidate_methods:
        fn = getattr(auth, name, None)
        available[name] = callable(fn)
        if callable(fn):
            try:
                signatures[name] = str(inspect.signature(fn))
            except Exception:
                signatures[name] = "<signature unavailable>"

record(
    "AUTH_VALIDATE_PRESENT",
    available.get("validate", False),
    signatures.get("validate"),
)

record(
    "AUTH_CREATE_OR_EQUIVALENT_PRESENT",
    available.get("create", False) or available.get("consume", False),
    {
        "create": signatures.get("create"),
        "consume": signatures.get("consume"),
    },
)

# Inspect class source for expiry / TTL / one-shot semantics.
source = ""

if auth is not None:
    try:
        source = inspect.getsource(type(auth))
    except Exception:
        source = ""

source_lower = source.lower()

record(
    "AUTH_SOURCE_REFERENCES_TTL_OR_EXPIRY",
    any(token in source_lower for token in ["ttl", "expire", "expires", "expiry"]),
    [token for token in ["ttl", "expire", "expires", "expiry"] if token in source_lower],
)

record(
    "AUTH_SOURCE_REFERENCES_ONE_SHOT_OR_CONSUME",
    any(token in source_lower for token in ["one_shot", "oneshot", "consume", "used"]),
    [token for token in ["one_shot", "oneshot", "consume", "used"] if token in source_lower],
)

# Verify orchestrator uses authorization before execution.
try:
    execute_source = inspect.getsource(orch.execute_once)
except Exception:
    execute_source = ""

exec_lower = execute_source.lower()

record(
    "EXECUTE_ONCE_CALLS_AUTH",
    "auth" in exec_lower and "validate" in exec_lower,
    "auth.validate referenced" if ("auth" in exec_lower and "validate" in exec_lower) else "missing",
)

record(
    "EXECUTE_ONCE_CONSUMES_AUTH",
    "consume" in exec_lower,
    "consume referenced" if "consume" in exec_lower else "not referenced",
)

# Verify no stale post-lock and fail-closed policy remains intact.
postlock = orch.postlock.status()

record(
    "POSTLOCK_CLEAR",
    not bool(postlock.get("locked", False)),
    postlock,
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
    "auth_type": type(auth).__name__ if auth else None,
    "available_methods": available,
    "method_signatures": signatures,
    "postlock": postlock,
    "readiness": readiness,
}

print("\n===== REPORT =====")
print(json.dumps(report, indent=2, default=str))

print("\n==========================================")
print(
    "PHASE61_AUTHORIZATION_LIFECYCLE_AUDIT:",
    "PASS" if not failed else "REVIEW_REQUIRED",
)
print("==========================================")
print("AUTHORIZATION_LAYER_PRESENT:", auth is not None)
print("AUTHORIZATION_VALIDATION_PRESENT:", available.get("validate", False))
print("AUTH_EXPIRY_OR_TTL_LOGIC_PRESENT:", any(token in source_lower for token in ["ttl", "expire", "expires", "expiry"]))
print("ONE_SHOT_OR_CONSUME_LOGIC_PRESENT:", any(token in source_lower for token in ["one_shot", "oneshot", "consume", "used"]))
print("ALLOWLIST_PRESERVED:", destination in orch.allowlist)
print("POSTLOCK_CLEAR:", not bool(postlock.get("locked", False)))
print("REAL_AUTH_CREATED: False")
print("TRANSACTION_CREATED: False")
print("TRANSACTION_SIGNED: False")
print("BROADCAST_ATTEMPTED: False")

raise SystemExit(0 if not failed else 2)
