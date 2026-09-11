import json
from companyos.runtime.idle_cycle_recovery_controller import empty_cycle_detected, runtime_state

eligible, detail = empty_cycle_detected(min_idle_cycles=25)
print(json.dumps({
    "runtime": runtime_state(),
    "idle_cycle_recovery_eligible": eligible,
    "detail": detail,
}, indent=2, default=str))
