from pathlib import Path
import inspect
import json

from companyos.liveintegration.live_orchestrator import FinalLiveExecutionOrchestrator

root = Path.home() / "companyos"

print("===== PHASE 63A: POSTLOCK STRUCTURE AUDIT =====")

orch = FinalLiveExecutionOrchestrator(root)
postlock = getattr(orch, "postlock", None)

checks = {}

def record(name, passed, detail=None):
    checks[name] = {"passed": bool(passed), "detail": detail}
    print(f"{name}: {bool(passed)}")
    if detail is not None:
        print("  detail:", detail)

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

source = ""
if postlock is not None:
    try:
        source = inspect.getsource(type(postlock))
    except Exception:
        source = ""

lower = source.lower()

record(
    "POSTLOCK_SOURCE_HAS_LOCKED_FIELD",
    "locked" in lower,
    "locked" in lower,
)

record(
    "POSTLOCK_SOURCE_HAS_REASON_FIELD",
    "reason" in lower,
    "reason" in lower,
)

record(
    "POSTLOCK_SOURCE_HAS_TIMESTAMP_FIELD",
    any(x in lower for x in ["timestamp", "locked_at", "time"]),
    [x for x in ["timestamp", "locked_at", "time"] if x in lower],
)

failed = [name for name, item in checks.items() if not item["passed"]]

print("\n===== SUMMARY =====")
print(json.dumps({
    "success": not failed,
    "failed_checks": failed,
    "postlock_type": type(postlock).__name__ if postlock else None,
    "methods": methods,
    "signatures": signatures,
    "state": state,
}, indent=2, default=str))

print("\n==========================================")
print(
    "PHASE63A_POSTLOCK_STRUCTURE_AUDIT:",
    "PASS" if not failed else "REVIEW_REQUIRED",
)
print("==========================================")
print("POSTLOCK_CLEAR:", not bool(state.get("locked", False)))
print("TRANSACTION_CREATED: False")
print("TRANSACTION_SIGNED: False")
print("BROADCAST_ATTEMPTED: False")

raise SystemExit(0 if not failed else 2)
