from pathlib import Path
import json
import inspect

from companyos.liveintegration.live_orchestrator import FinalLiveExecutionOrchestrator
from companyos.walletsource.identity_loader import VerifiedWalletIdentity

root = Path.home() / "companyos"

print("===== PHASE 62: RECEIPT & RECONCILIATION AUDIT =====")

identity = VerifiedWalletIdentity(root).load()
assert identity.get("success") is True, identity

destination = identity.get("public_address")
assert destination, "VERIFIED_PUBLIC_ADDRESS_MISSING"

orch = FinalLiveExecutionOrchestrator(root)

checks = {}

def record(name, passed, detail=None):
    checks[name] = {
        "passed": bool(passed),
        "detail": detail,
    }
    print(f"{name}: {bool(passed)}")
    if detail is not None:
        print("  detail:", detail)

receipts = getattr(orch, "receipts", None)
reconciler = getattr(orch, "reconciler", None)

record(
    "RECEIPT_COMPONENT_PRESENT",
    receipts is not None,
    type(receipts).__name__ if receipts else "MISSING",
)

record(
    "RECONCILER_COMPONENT_PRESENT",
    reconciler is not None,
    type(reconciler).__name__ if reconciler else "MISSING",
)

# Capture receipt methods.
receipt_methods = {}
receipt_signatures = {}

if receipts is not None:
    for name in ["append", "recent", "read", "list", "status"]:
        fn = getattr(receipts, name, None)
        receipt_methods[name] = callable(fn)
        if callable(fn):
            try:
                receipt_signatures[name] = str(inspect.signature(fn))
            except Exception:
                receipt_signatures[name] = "<signature unavailable>"

record(
    "RECEIPT_APPEND_PRESENT",
    receipt_methods.get("append", False),
    receipt_signatures.get("append"),
)

# Capture reconciler methods.
reconciler_methods = {}
reconciler_signatures = {}

if reconciler is not None:
    for name in ["reconcile", "verify", "status"]:
        fn = getattr(reconciler, name, None)
        reconciler_methods[name] = callable(fn)
        if callable(fn):
            try:
                reconciler_signatures[name] = str(inspect.signature(fn))
            except Exception:
                reconciler_signatures[name] = "<signature unavailable>"

record(
    "RECONCILER_METHOD_PRESENT",
    any(reconciler_methods.values()),
    reconciler_signatures,
)

# Inspect orchestrator source to ensure receipts and reconciliation are part of the flow.
try:
    source = inspect.getsource(orch.execute_once)
except Exception:
    source = ""

source_lower = source.lower()

record(
    "EXECUTE_ONCE_REFERENCES_RECEIPTS",
    "receipt" in source_lower,
    "receipt" in source_lower,
)

record(
    "EXECUTE_ONCE_REFERENCES_RECONCILIATION_OR_VERIFICATION",
    ("reconcile" in source_lower) or ("verification" in source_lower) or ("verify" in source_lower),
    {
        "reconcile": "reconcile" in source_lower,
        "verification": "verification" in source_lower,
        "verify": "verify" in source_lower,
    },
)

# Check persistent receipt files without modifying them.
receipt_files = [
    root / "companyos_runtime" / "liveexec_receipts.jsonl",
    root / "companyos_runtime" / "execution_receipts.jsonl",
    root / "companyos_runtime" / "controlled_execution_receipts.jsonl",
]

receipt_file_state = {}

for p in receipt_files:
    receipt_file_state[str(p)] = {
        "exists": p.exists(),
        "size": p.stat().st_size if p.exists() else 0,
    }

record(
    "RECEIPT_STORAGE_PATHS_INSPECTED",
    True,
    receipt_file_state,
)

# Postlock must still be clear.
postlock = orch.postlock.status()

record(
    "POSTLOCK_CLEAR",
    not bool(postlock.get("locked", False)),
    postlock,
)

# Treasury policy must remain fail-closed.
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

# Readiness snapshot only.
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

failed = [
    name
    for name, item in checks.items()
    if not item["passed"]
]

report = {
    "success": not failed,
    "failed_checks": failed,
    "receipt_type": type(receipts).__name__ if receipts else None,
    "receipt_methods": receipt_methods,
    "receipt_signatures": receipt_signatures,
    "reconciler_type": type(reconciler).__name__ if reconciler else None,
    "reconciler_methods": reconciler_methods,
    "reconciler_signatures": reconciler_signatures,
    "receipt_files": receipt_file_state,
    "postlock": postlock,
    "readiness": readiness,
}

print("\n===== REPORT =====")
print(json.dumps(report, indent=2, default=str))

print("\n==========================================")
print(
    "PHASE62_RECEIPT_RECONCILIATION_AUDIT:",
    "PASS" if not failed else "REVIEW_REQUIRED",
)
print("==========================================")
print("RECEIPT_LAYER_PRESENT:", receipts is not None)
print("RECONCILIATION_LAYER_PRESENT:", reconciler is not None)
print("RECEIPT_APPEND_PRESENT:", receipt_methods.get("append", False))
print("POSTLOCK_CLEAR:", not bool(postlock.get("locked", False)))
print("REAL_AUTH_CREATED: False")
print("TRANSACTION_CREATED: False")
print("TRANSACTION_SIGNED: False")
print("BROADCAST_ATTEMPTED: False")

raise SystemExit(0 if not failed else 2)
