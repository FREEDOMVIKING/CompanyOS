#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos_phase561_576 import (
    BusinessCase,VentureScorecard,StageEvidence,CommitmentGate,LaunchReadiness,
    OperatingKPIs,PortfolioCompare,CapitalAttention,KillScalePolicy,MilestoneEngine,
    ExecutionAudit,MissionAuditBridge,BusinessExecutionManager,PortfolioIntelligence,
    CEOExecutionBridge,ExecutionRuntime
)

venture={"venture_id":"v1","name":"X","stage":"validation","brief":{"product_name":"X"}}
evidence={
    "validation_decision":"go_to_mvp",
    "validation_score":8,
    "activation_rate":0.3,
    "retention_rate":0.35,
    "revenue_signal":4,
    "critical_issues":0,
}

assert BusinessCase().build(venture)["venture_id"]=="v1"
assert VentureScorecard().score(evidence)["score"]>0
assert StageEvidence().evaluate("validation",evidence)["ready"] is True
assert CommitmentGate().evaluate("validation",evidence)["commitment_allowed"] is True
assert LaunchReadiness().evaluate({
    "release_candidate_ready":True,"targeted_tests_pass":True,"regression_tests_pass":True,
    "telemetry_ready":True,"rollback_ready":True,"support_path_ready":True
})["ready"] is True
assert OperatingKPIs().calculate({"qualified_visitors":100,"activated_users":25,"paying_customers":5,"retained_customers":4,"customers_start":5})["activation_rate"]==0.25
ranked=PortfolioCompare().rank([{"venture_id":"a","score":8},{"venture_id":"b","score":5}])
assert ranked[0]["venture_id"]=="a"
assert CapitalAttention().allocate(ranked,1)["active_attention"]==["a"]
assert KillScalePolicy().decide(evidence)["decision"] in ("scale","iterate","research_or_validate_more","kill_or_pause")
assert MilestoneEngine().next("validation")=="build"

root=Path(tempfile.mkdtemp(prefix="phase576_"))
assert ExecutionAudit(root).append("x",{})["event"]=="x"
assert MissionAuditBridge(root).record("m","research",{"success":True})["mission_id"]=="m"
assert BusinessExecutionManager().review(venture,evidence)["success"] is True
assert PortfolioIntelligence().analyze([{"venture_id":"v1","evidence":evidence}])["success"] is True
assert CEOExecutionBridge().venture_review(venture,evidence)["status"]=="business_execution_review_ready"
assert ExecutionRuntime().status()["success"] is True

print(json.dumps({
    "success":True,
    "status":"phase561_576_verification_passed",
    "cycle_status":"phase576_business_execution_portfolio_intelligence_ready",
    "business_case_engine":True,
    "venture_scorecards":True,
    "stage_evidence_gates":True,
    "commitment_gates":True,
    "launch_readiness":True,
    "operating_kpis":True,
    "portfolio_comparison":True,
    "kill_scale_policy":True,
    "mission_audit_bridge":True,
    "autonomy_mode":"high"
},indent=2))
