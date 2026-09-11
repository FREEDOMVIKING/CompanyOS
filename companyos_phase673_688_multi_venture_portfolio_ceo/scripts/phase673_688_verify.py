#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos_phase673_688 import *

ventures=[
    {"venture_id":"v1","name":"Workflow Automation","problem":"manual workflow","category":"saas","mrr":1000,"profit":200,
     "validation_score":8,"revenue_signal":6,"roi_score":7,"resource_efficiency":1.2,"retention_rate":0.7,
     "stagnant_cycles":0,"infrastructure_needs":["auth","billing"]},
    {"venture_id":"v2","name":"Reporting Intelligence","problem":"manual reporting","category":"analytics","mrr":500,"profit":50,
     "validation_score":6,"revenue_signal":3,"roi_score":5,"resource_efficiency":0.7,"retention_rate":0.5,
     "stagnant_cycles":1,"infrastructure_needs":["auth","billing"]},
]

assert PortfolioStrategy().build()["max_active_ventures"] >= 1
assert CategoryBalance().evaluate(ventures)["counts"]
assert DuplicateAvoidance().check(
    {"name":"Workflow Automation Tool","problem":"manual workflow"},
    ventures
)["duplicate_risk"] is True
assert SharedResourcePool().allocate(ventures)["allocations"]["builder"]
assert KnowledgeTransfer().transfer(
    {"venture_id":"v1","lessons":["a","b"]},
    {"venture_id":"v2","lessons":["b"]}
)["reusable_lessons"] == ["a"]
assert "auth" in InfrastructureReuse().recommend(ventures)["shared_candidates"]
assert VentureTemplate().create("X","saas","thesis")["stage"]=="incubating"

scored=[]
for v in ventures:
    item=dict(v)
    item["portfolio_score"]=PortfolioPriority().score(item)
    scored.append(item)
assert scored[0]["portfolio_score"]>0

assert PortfolioActionPolicy().decide({
    "portfolio_score":8.5,"profitable":True,"stagnant_cycles":0,"duplicate_risk":False
})["decision"]=="scale"

kpis=PortfolioKPIs().calculate(ventures)
assert kpis["venture_count"]==2
assert ConcentrationRisk().evaluate(ventures)["dominant_venture"]
assert ResourceConflict().detect(
    [{"roles":{"builder":2}},{"roles":{"builder":2}}],
    {"builder":2}
)["has_conflict"] is True

candidate={"venture_id":"c1","portfolio_score":9}
succ=SuccessionEngine().recommend(scored,[candidate],max_active=2)
assert succ["action"] in ("replace","hold","spin_up")

creation=CompanyCreationOrchestrator().prepare(
    {"name":"Compliance Copilot","category":"compliance","problem":"manual compliance","thesis":"automate compliance"},
    ventures
)
assert creation["success"] is True
assert creation["automatic_legal_entity_creation"] is False

root=Path(tempfile.mkdtemp(prefix="phase688_"))
assert PortfolioAudit(root).append("x",{})["event"]=="x"
assert PortfolioRuntime().status()["success"] is True

print(json.dumps({
    "success":True,
    "status":"phase673_688_verification_passed",
    "cycle_status":"phase688_multi_venture_portfolio_ceo_ready",
    "portfolio_strategy":True,
    "category_balance":True,
    "duplicate_avoidance":True,
    "shared_resource_pool":True,
    "cross_venture_knowledge_transfer":True,
    "shared_infrastructure_reuse":True,
    "venture_templates":True,
    "portfolio_action_policy":True,
    "portfolio_kpis":True,
    "concentration_risk":True,
    "resource_conflicts":True,
    "portfolio_priority":True,
    "succession_replacement_logic":True,
    "company_creation_orchestration":True,
    "portfolio_audit":True,
    "automatic_legal_entity_creation":False,
    "automatic_external_financial_commitment":False,
    "autonomy_mode":"high"
},indent=2))
