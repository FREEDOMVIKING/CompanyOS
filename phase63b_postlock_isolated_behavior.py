from pathlib import Path
from tempfile import TemporaryDirectory
import json

from companyos.controlledexec.postlock import PostExecutionLock

print("===== PHASE 63B: POSTLOCK ISOLATED BEHAVIOR TEST =====")

checks = {}

def record(name, passed, detail=None):
    checks[name] = {
        "passed": bool(passed),
        "detail": detail,
    }
    print(f"{name}: {bool(passed)}")
    if detail is not None:
        print("  detail:", detail)

with TemporaryDirectory(prefix="companyos_phase63b_") as td:
    test_root = Path(td)

    # Create isolated lock store completely outside the real CompanyOS runtime.
    lock1 = PostExecutionLock(test_root)

    initial = lock1.status()

    record(
        "INITIAL_STATE_READABLE",
        isinstance(initial, dict),
        initial,
    )

    record(
        "INITIAL_STATE_CLEAR",
        not bool(initial.get("locked", False)),
        initial.get("locked"),
    )

    # Engage isolated lock.
    engage = lock1.engage("phase63b_isolated_test")

    record(
        "ENGAGE_RETURNED_SUCCESS",
        isinstance(engage, dict) and bool(engage.get("success", False)),
        engage,
    )

    engaged_state = lock1.status()

    record(
        "LOCK_BECAME_ACTIVE",
        bool(engaged_state.get("locked", False)),
        engaged_state,
    )

    record(
        "LOCK_REASON_PERSISTED",
        engaged_state.get("reason") == "phase63b_isolated_test",
        engaged_state.get("reason"),
    )

    # Re-open from a fresh object to verify file persistence semantics.
    lock2 = PostExecutionLock(test_root)
    reopened = lock2.status()

    record(
        "LOCK_PERSISTS_ACROSS_FRESH_INSTANCE",
        bool(reopened.get("locked", False)),
        reopened,
    )

    record(
        "PERSISTED_REASON_SURVIVES_RELOAD",
        reopened.get("reason") == "phase63b_isolated_test",
        reopened.get("reason"),
    )

    # Clear isolated lock.
    cleared = lock2.clear()

    record(
        "CLEAR_RETURNED_SUCCESS",
        isinstance(cleared, dict) and bool(cleared.get("success", False)),
        cleared,
    )

    cleared_state = lock2.status()

    record(
        "LOCK_CLEARED",
        not bool(cleared_state.get("locked", False)),
        cleared_state,
    )

    # Fresh instance after clear must also see clear state.
    lock3 = PostExecutionLock(test_root)
    final_state = lock3.status()

    record(
        "CLEAR_PERSISTS_ACROSS_FRESH_INSTANCE",
        not bool(final_state.get("locked", False)),
        final_state,
    )

failed = [
    name
    for name, result in checks.items()
    if not result["passed"]
]

summary = {
    "success": not failed,
    "failed_checks": failed,
    "checks": checks,
}

print("\n===== SUMMARY =====")
print(json.dumps(summary, indent=2, default=str))

print("\n==========================================")
print(
    "PHASE63B_POSTLOCK_ISOLATED_BEHAVIOR:",
    "PASS" if not failed else "REVIEW_REQUIRED",
)
print("==========================================")
print("ISOLATED_TEST_ROOT_USED: True")
print("REAL_COMPANYOS_LOCK_TOUCHED: False")
print("LOCK_ENGAGE_VERIFIED:", checks.get("LOCK_BECAME_ACTIVE", {}).get("passed", False))
print("LOCK_PERSISTENCE_VERIFIED:", checks.get("LOCK_PERSISTS_ACROSS_FRESH_INSTANCE", {}).get("passed", False))
print("LOCK_CLEAR_VERIFIED:", checks.get("LOCK_CLEARED", {}).get("passed", False))
print("TRANSACTION_CREATED: False")
print("TRANSACTION_SIGNED: False")
print("BROADCAST_ATTEMPTED: False")

raise SystemExit(0 if not failed else 2)
