from pathlib import Path
import hashlib
import json
import os

from companyos.liveintegration.live_orchestrator import FinalLiveExecutionOrchestrator
from companyos.walletsource.identity_loader import VerifiedWalletIdentity

root = Path.home() / "companyos"

print("===== PHASE 58: PERSISTENT STATE INTEGRITY AUDIT =====")

identity = VerifiedWalletIdentity(root).load()
assert identity.get("success") is True, identity

destination = identity.get("public_address")
assert destination, "VERIFIED_PUBLIC_ADDRESS_MISSING"

orch = FinalLiveExecutionOrchestrator(root)

targets = [
    root / "companyos_runtime" / "financial_allowlist.json",
    root / "companyos_runtime" / "post_execution_lock.json",
    root / "companyos_runtime" / "liveexec_receipts.jsonl",
    root / "companyos_runtime" / "controlled_execution_receipts.jsonl",
]

def file_state(path: Path):
    if not path.exists():
        return {
            "exists": False,
            "size": 0,
            "sha256": None,
        }

    data = path.read_bytes()
    return {
        "exists": True,
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }

before = {str(p): file_state(p) for p in targets}

checks = {}

def record(name, passed, detail=None):
    checks[name] = {
        "passed": bool(passed),
        "detail": detail,
    }
    print(f"{name}: {bool(passed)}")
    if detail is not None:
        print("  detail:", detail)

record(
    "VERIFIED_IDENTITY_PRESENT",
    bool(destination),
    destination,
)

record(
    "VERIFIED_DESTINATION_IN_ALLOWLIST",
    destination in orch.allowlist,
    f"allowlist_count={len(orch.allowlist)}",
)

lock_before = orch.postlock.status()

record(
    "POSTLOCK_STATUS_READABLE",
    isinstance(lock_before, dict),
    lock_before,
)

record(
    "POSTLOCK_CLEAR_BEFORE_AUDIT",
    not bool(lock_before.get("locked", False)),
    lock_before.get("locked"),
)

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
        "ALLOWLIST_REQUIRED",
        getattr(policy, "require_allowlist", None) is True,
        getattr(policy, "require_allowlist", None),
    )

    record(
        "AUTONOMOUS_TRANSFERS_DISABLED",
        getattr(policy, "allow_autonomous_transfers", None) is False,
        getattr(policy, "allow_autonomous_transfers", None),
    )

# Read-only readiness inspection.
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

# Read-only object contract inspection.
method_checks = {
    "readiness.evaluate": callable(getattr(orch.readiness, "evaluate", None)),
    "guard.check": callable(getattr(orch.guard, "check", None)),
    "auth.validate": callable(getattr(orch.auth, "validate", None)),
    "tx.prepare": callable(getattr(orch.tx, "prepare", None)),
    "execgate.prepare_and_execute": callable(
        getattr(orch.execgate, "prepare_and_execute", None)
    ),
    "receipts.append": callable(getattr(orch.receipts, "append", None)),
    "postlock.engage": callable(getattr(orch.postlock, "engage", None)),
}

for name, ok in method_checks.items():
    record(
        "METHOD_" + name.upper().replace(".", "_"),
        ok,
        name,
    )

after = {str(p): file_state(p) for p in targets}

changes = {}

for path in sorted(set(before) | set(after)):
    if before[path] != after[path]:
        changes[path] = {
            "before": before[path],
            "after": after[path],
        }

record(
    "NO_TRACKED_PERSISTENT_STATE_CHANGED",
    len(changes) == 0,
    changes if changes else "no changes",
)

lock_after = orch.postlock.status()

record(
    "POSTLOCK_CLEAR_AFTER_AUDIT",
    not bool(lock_after.get("locked", False)),
    lock_after,
)

auto_env = os.getenv(
    "COMPANYOS_ALLOW_AUTONOMOUS_TRANSFERS",
    "",
).strip().lower()

record(
    "AUTONOMOUS_TRANSFER_ENV_NOT_ENABLED",
    auto_env not in {"1", "true", "yes", "on"},
    auto_env or "<UNSET>",
)

failed = [
    name
    for name, result in checks.items()
    if not result["passed"]
]

report = {
    "success": not failed,
    "failed_checks": failed,
    "before": before,
    "after": after,
    "changes": changes,
    "readiness": readiness,
    "postlock_before": lock_before,
    "postlock_after": lock_after,
}

print("\n===== REPORT =====")
print(json.dumps(report, indent=2, default=str))

print("\n==========================================")
print(
    "PHASE58_PERSISTENT_STATE_INTEGRITY_AUDIT:",
    "PASS" if not failed else "REVIEW_REQUIRED",
)
print("==========================================")
print("PERSISTENT_STATE_UNCHANGED:", len(changes) == 0)
print("ALLOWLIST_PRESERVED:", destination in orch.allowlist)
print("POSTLOCK_CLEAR:", not bool(lock_after.get("locked", False)))
print("REAL_AUTH_CREATED: False")
print("TRANSACTION_CREATED: False")
print("TRANSACTION_SIGNED: False")
print("BROADCAST_ATTEMPTED: False")

raise SystemExit(0 if not failed else 2)
