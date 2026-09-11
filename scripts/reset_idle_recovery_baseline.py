from companyos.runtime.idle_cycle_recovery_controller import runtime_state, save, STATE
import json

rt = runtime_state()
cycle_count = int(rt.get("cycle_count", 0) or 0)
active = int(rt.get("active_orchestrations", 0) or 0)
dispatched = int(rt.get("cycles_dispatched_this_tick", 0) or 0)
last_oid = rt.get("last_orchestration_id")

seed = cycle_count
if active == 0 and dispatched == 0 and not last_oid and cycle_count >= 25:
    seed = max(0, cycle_count - 25)

old = {}
try:
    old = json.loads(STATE.read_text(encoding="utf-8"))
except Exception:
    pass

new = {
    "last_cycle_count": cycle_count,
    "last_productive_cycle_count": seed,
    "recoveries": old.get("recoveries", []),
    "last_recovery_unix": old.get("last_recovery_unix", 0),
}
save(STATE, new)
print(json.dumps({
    "IDLE_RECOVERY_BASELINE_RESET": True,
    "cycle_count": cycle_count,
    "last_productive_cycle_count": seed,
    "immediately_eligible_if_still_idle": (cycle_count - seed) >= 25,
}, indent=2))
