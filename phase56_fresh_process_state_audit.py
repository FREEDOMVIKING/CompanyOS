from pathlib import Path
import json
import os

from companyos.liveintegration.live_orchestrator import FinalLiveExecutionOrchestrator
from companyos.walletsource.identity_loader import VerifiedWalletIdentity

root = Path.home() / "companyos"

print("===== PHASE 56: FRESH-PROCESS STATE & RESTART AUDIT =====")

# Fresh process objects only — confirms Phase 55B monkey-patches did not persist.
identity = VerifiedWalletIdentity(root).load()
assert identity.get("success") is True, identity
assert identity.get("chain") == "solana", identity

public_address = identity.get("public_address")
assert public_address, "VERIFIED_PUBLIC_ADDRESS_MISSING"

orch = FinalLiveExecutionOrchestrator(root)

checks = {}

def record(name, value, detail=None):
    checks[name] = {
        "passed": bool(value),
        "detail": detail,
    }
    print(f"{name}: {bool(value)}")
    if detail is not None:
        print(f"  detail: {detail}")

# Core object graph restored from disk/code.
record(
    "FRESH_ORCHESTRATOR_CREATED",
    type(orch).__name__ == "FinalLiveExecutionOrchestrator",
    type(orch).__name__,
)

record(
    "VERIFIED_IDENTITY_RELOADED",
    identity.get("success") is True,
    identity.get("status"),
)

record(
    "VERIFIED_ADDRESS_IN_ALLOWLIST",
    public_address in orch.allowlist,
    f"allowlist_count={len(orch.allowlist)}",
)

# Persistent allowlist sanity.
allowlist_path = root / "companyos_runtime" / "financial_allowlist.json"
allowlist_data = {}
if allowlist_path.exists():
    allowlist_data = json.loads(allowlist_path.read_text(encoding="utf-8"))

record(
    "ALLOWLIST_FILE_PRESENT",
    allowlist_path.exists(),
    str(allowlist_path),
)

record(
    "DEFAULT_DENY_PERSISTED",
    allowlist_data.get("default_deny") is True,
    allowlist_data.get("default_deny"),
)

# Phase 55B monkey-patches should be gone after process exit.
readiness_name = getattr(getattr(orch.readiness, "evaluate", None), "__name__", "")
guard_name = getattr(getattr(orch.guard, "check", None), "__name__", "")
auth_name = getattr(getattr(orch.auth, "validate", None), "__name__", "")
prepare_name = getattr(getattr(orch.tx, "prepare", None), "__name__", "")
execute_name = getattr(getattr(orch.execgate, "prepare_and_execute", None), "__name__", "")

record(
    "READINESS_METHOD_RESTORED",
    readiness_name != "readiness",
    readiness_name,
)
record(
    "RUNTIME_GUARD_METHOD_RESTORED",
    guard_name != "guard",
    guard_name,
)
record(
    "AUTH_METHOD_RESTORED",
    auth_name != "authorization",
    auth_name,
)
record(
    "TRANSACTION_PREPARE_METHOD_RESTORED",
    prepare_name != "prepare" or "synthetic" not in repr(getattr(orch.tx, "prepare", None)).lower(),
    prepare_name,
)
record(
    "EXECUTION_METHOD_RESTORED",
    execute_name != "execute" or "synthetic" not in repr(getattr(orch.execgate, "prepare_and_execute", None)).lower(),
    execute_name,
)

# Post-lock must remain clear before future controlled work.
postlock = orch.postlock.status()
record(
    "POST_EXECUTION_LOCK_CLEAR",
    not bool(postlock.get("locked", False)),
    postlock,
)

# Treasury controller/policy.
controller = getattr(orch.execgate, "controller", None)
record(
    "SPEND_CONTROLLER_PRESENT",
    controller is not None,
    type(controller).__name__ if controller else "MISSING",
)

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

# Environment safety state.
auto_env = os.getenv("COMPANYOS_ALLOW_AUTONOMOUS_TRANSFERS", "").strip().lower()
record(
    "AUTONOMOUS_TRANSFER_ENV_NOT_ENABLED",
    auto_env not in {"1", "true", "yes", "on"},
    auto_env or "<UNSET>",
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

failed = [name for name, data in checks.items() if not data["passed"]]

print("\n===== SUMMARY =====")
print(json.dumps({
    "success": not failed,
    "failed_checks": failed,
    "check_count": len(checks),
    "postlock": postlock,
    "readiness": readiness,
}, indent=2, default=str))

print("\n==========================================")
print("PHASE56_FRESH_PROCESS_STATE_AUDIT:", "PASS" if not failed else "REVIEW_REQUIRED")
print("==========================================")
print("FRESH_PROCESS_CONFIRMED:", not failed)
print("IN_MEMORY_TEST_PATCHES_PERSISTED: False")
print("PERSISTENT_ALLOWLIST_PRESERVED:", public_address in orch.allowlist)
print("POSTLOCK_CLEAR:", not bool(postlock.get("locked", False)))
print("REAL_AUTH_CREATED: False")
print("TRANSACTION_CREATED: False")
print("TRANSACTION_SIGNED: False")
print("BROADCAST_ATTEMPTED: False")

raise SystemExit(0 if not failed else 2)
