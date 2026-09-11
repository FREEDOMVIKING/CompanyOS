from pathlib import Path
import inspect
import json

from companyos.liveintegration.live_orchestrator import FinalLiveExecutionOrchestrator
from companyos.walletsource.identity_loader import VerifiedWalletIdentity

root = Path.home() / "companyos"

print("===== PHASE 57: EXECUTION CONTRACT AUDIT =====")

identity = VerifiedWalletIdentity(root).load()
assert identity.get("success") is True, identity

destination = identity.get("public_address")
assert destination, "VERIFIED_SOLANA_ADDRESS_MISSING"

orch = FinalLiveExecutionOrchestrator(root)

checks = {}
contracts = {}

def record(name, passed, detail=None):
    checks[name] = {"passed": bool(passed), "detail": detail}
    print(f"{name}: {bool(passed)}")
    if detail is not None:
        print("  detail:", detail)

def signature_of(obj, name):
    fn = getattr(obj, name, None)
    if not callable(fn):
        return None
    try:
        return str(inspect.signature(fn))
    except Exception:
        return "<signature unavailable>"

# Core public method contracts
targets = [
    ("readiness.evaluate", orch.readiness, "evaluate"),
    ("guard.check", orch.guard, "check"),
    ("auth.validate", orch.auth, "validate"),
    ("tx.prepare", orch.tx, "prepare"),
    ("execgate.prepare_and_execute", orch.execgate, "prepare_and_execute"),
    ("receipts.append", orch.receipts, "append"),
    ("postlock.engage", orch.postlock, "engage"),
    ("postlock.status", orch.postlock, "status"),
    ("orchestrator.execute_once", orch, "execute_once"),
]

for label, obj, method in targets:
    fn = getattr(obj, method, None)
    sig = signature_of(obj, method)
    contracts[label] = {
        "present": callable(fn),
        "signature": sig,
        "owner_type": type(obj).__name__,
    }
    record(
        f"CONTRACT_{label.replace('.', '_').upper()}",
        callable(fn),
        sig,
    )

# Fresh process sanity
record(
    "VERIFIED_DESTINATION_IN_ALLOWLIST",
    destination in orch.allowlist,
    f"allowlist_count={len(orch.allowlist)}",
)

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
    policy_snapshot = {
        "autonomous_single_tx_limit": getattr(policy, "autonomous_single_tx_limit", None),
        "autonomous_daily_limit": getattr(policy, "autonomous_daily_limit", None),
        "reserve_floor": getattr(policy, "reserve_floor", None),
        "max_daily_loss": getattr(policy, "max_daily_loss", None),
        "require_allowlist": getattr(policy, "require_allowlist", None),
        "allow_autonomous_transfers": getattr(policy, "allow_autonomous_transfers", None),
    }
else:
    policy_snapshot = {}

# Source-level field contract for execute_once.
execute_src = ""
try:
    execute_src = inspect.getsource(orch.execute_once)
except Exception:
    execute_src = ""

required_tokens = [
    "readiness",
    "guard",
    "check_amount",
    "auth",
    "tx.prepare",
    "source",
    "fingerprint",
    "prepare_and_execute",
    "receipts",
    "postlock",
]

source_contract = {}
for token in required_tokens:
    present = token in execute_src
    source_contract[token] = present
    record(
        f"EXECUTE_ONCE_SOURCE_HAS_{token.upper().replace('.', '_')}",
        present,
        token,
    )

# Ensure no stale post-lock
postlock = orch.postlock.status()
record(
    "POSTLOCK_CLEAR",
    not bool(postlock.get("locked", False)),
    postlock,
)

# Readiness snapshot only; no transaction path invoked.
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
    "contracts": contracts,
    "policy": policy_snapshot,
    "execute_once_source_contract": source_contract,
    "postlock": postlock,
    "readiness": readiness,
}

print("\n===== REPORT =====")
print(json.dumps(report, indent=2, default=str))

print("\n==========================================")
print("PHASE57_EXECUTION_CONTRACT_AUDIT:", "PASS" if not failed else "REVIEW_REQUIRED")
print("==========================================")
print("METHOD_SIGNATURES_CAPTURED: True")
print("EXECUTE_ONCE_CONTRACT_MAPPED: True")
print("ALLOWLIST_PRESERVED:", destination in orch.allowlist)
print("POSTLOCK_CLEAR:", not bool(postlock.get("locked", False)))
print("REAL_AUTH_CREATED: False")
print("TRANSACTION_CREATED: False")
print("TRANSACTION_SIGNED: False")
print("BROADCAST_ATTEMPTED: False")

raise SystemExit(0 if not failed else 2)
