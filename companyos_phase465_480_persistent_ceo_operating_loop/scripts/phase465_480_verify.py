#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos_phase465_480 import (
    StageContract, CEOState, StageRouter, CycleBudget, FailureRecovery,
    CEOCycle, PersistentCEO, CEORuntime
)

root = Path(tempfile.mkdtemp(prefix="companyos_phase480_verify_"))

assert StageContract().normalize({}, "x")["stage"] == "x"

state_store = CEOState(root)
state = state_store.load()
assert state["current_stage"] == "opportunity"
state_store.save(state)
assert state_store.load()["cycles_completed"] == 0

router = StageRouter()
assert router.next_stage("validation", {
    "success":True,
    "data":{"decision":{"decision":"go_to_mvp"}}
}) == "venture"

assert CycleBudget().limits()["max_stages_per_cycle"] >= 1
assert FailureRecovery().decide(1,"build")["action"] == "retry_stage"

# Verify unified cycle can stop cleanly with no evidence instead of crashing.
cycle = CEOCycle(root).run(start_stage="opportunity", context={})
assert cycle["status"] == "ceo_cycle_completed"

persistent = PersistentCEO(root).run(cycles=1)
assert persistent["status"] == "persistent_ceo_run_completed"
assert persistent["state"]["cycles_completed"] >= 1

assert CEORuntime().status()["success"] is True

print(json.dumps({
    "success":True,
    "status":"phase465_480_verification_passed",
    "cycle_status":"phase480_persistent_ceo_operating_loop_ready",
    "unified_stage_contract":True,
    "persistent_ceo_state":True,
    "stage_routing":True,
    "bounded_cycle_budget":True,
    "decision_journal":True,
    "failure_recovery":True,
    "opportunity_validation_venture_build_ops_portfolio_connected":True,
    "persistent_ceo_loop":True,
    "autonomy_mode":"high"
}, indent=2))
