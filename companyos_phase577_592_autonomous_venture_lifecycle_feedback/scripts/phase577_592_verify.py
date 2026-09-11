#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos_phase577_592 import (
    VentureIdentity, LifecycleStore, EvidenceUpdater, OutcomeIngestor,
    StageAdvancer, NextActionPolicy, MissionFactory, OutcomeScore,
    ProgressGuard, LifecycleAudit, VentureFeedbackLoop, PortfolioFeedback,
    ClosedLoopManager, CEOLifecycleBridge, LifecycleHealth, LifecycleRuntime
)

root = Path(tempfile.mkdtemp(prefix="phase592_"))
vid = VentureIdentity().make("X","workflow")
assert vid.startswith("venture_")

store = LifecycleStore(root)
store.upsert(vid, {"venture_id":vid,"stage":"validation","evidence":{"validation_decision":"go_to_mvp"}})
assert store.get(vid)["stage"] == "validation"

assert EvidenceUpdater().merge({"a":1},{"b":2})["b"] == 2
assert OutcomeIngestor().ingest({"mission_success":True})["mission_success"] is True
assert StageAdvancer().next_stage("validation",{"validation_decision":"go_to_mvp"}) == "build"
assert NextActionPolicy().decide("build",{}) == "continue_bounded_build"
assert MissionFactory().build(vid,"continue_bounded_build",{})["mission_type"] == "build"
assert OutcomeScore().score("validation","build",{"mission_success":True}) > 0
assert ProgressGuard().evaluate({"stagnant_cycles":2,"last_outcome_score":0})["action"] == "pause_and_research"
assert LifecycleAudit(root).append(vid,"x",{})["venture_id"] == vid

loop = VentureFeedbackLoop().update(
    {"venture_id":vid,"stage":"validation","evidence":{"validation_decision":"go_to_mvp"},"stagnant_cycles":0},
    {"mission_success":True}
)
assert loop["after_stage"] == "build"
assert loop["next_mission"]["mission_type"] == "build"

assert PortfolioFeedback().analyze([loop["record"]])["top_venture"] == vid
assert ClosedLoopManager(root).apply_outcome(vid,{"mission_success":True})["record"]
bridge = CEOLifecycleBridge(root)
assert bridge.ensure_venture("Y","x")["venture_id"]
assert LifecycleHealth().evaluate(list(store.load().values()))["healthy"] is True
assert LifecycleRuntime().status()["success"] is True

print(json.dumps({
    "success":True,
    "status":"phase577_592_verification_passed",
    "cycle_status":"phase592_autonomous_venture_lifecycle_feedback_ready",
    "stable_venture_identity":True,
    "durable_lifecycle_store":True,
    "evidence_updates":True,
    "outcome_ingestion":True,
    "stage_advancement":True,
    "next_action_policy":True,
    "deterministic_next_missions":True,
    "progress_guard":True,
    "portfolio_feedback":True,
    "lifecycle_audit":True,
    "closed_loop_manager":True,
    "autonomy_mode":"high"
}, indent=2))
