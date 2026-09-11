import json
from companyos.runtime.profit_first_dispatcher import should_dispatch, runtime_state, dispatcher_state

eligible, detail = should_dispatch(min_idle_cycles=20, cooldown_seconds=300)
print(json.dumps({
    "runtime": runtime_state(),
    "dispatcher_state": dispatcher_state(),
    "profit_first_dispatch_eligible": eligible,
    "detail": detail,
}, indent=2, default=str))
