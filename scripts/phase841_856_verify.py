#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos_phase841_856 import *

root=Path(tempfile.mkdtemp(prefix="phase856_"))
mission={
    "mission_id":"m1",
    "mission_type":"validation",
    "attempts":0,
    "context":{
        "venture_id":"v1",
        "research_confidence":0.82,
        "research_packet":{
            "confidence":0.82,
            "contradictions":{"topics":[]},
            "evidence":[
                {"id":"1","source_class":"official","tags":["problem","risk"]},
                {"id":"2","source_class":"reputable_news","tags":["demand","alternatives"]},
                {"id":"3","source_class":"competitor_site","tags":["pricing"],"willingness_to_pay_score":1.0},
                {"id":"4","source_class":"official","tags":["problem","demand"]},
                {"id":"5","source_class":"public_web","tags":["pricing","alternatives"],"willingness_to_pay_score":0.8},
            ]
        }
    }
}
a=ValidationMissionAdapter().adapt(mission); assert a["venture_id"]=="v1"
h=HypothesisExtractor().extract(a); assert len(h["hypotheses"])==3
assert len(ExperimentPlanner().plan(h))==3
assert ValidationMethodSelector().select("pricing")=="pricing_test"
assert ProblemEvidenceScore().score(a["research_packet"])>=0
assert PricingValidation().score(a["research_packet"])>=0
assert "differentiation_risk" in AlternativeComparison().evaluate(a["research_packet"])
assert FalsePositiveGuard().evaluate(a["research_packet"])["passed"] is True
assert ContradictionHandler().evaluate(a["research_packet"])["resolved"] is True
c=ValidationConfidence().score(0.8,0.8,0.8,0,True); assert c>0.7
assert DecisionThreshold().decide(0.8,True,True)["decision"]=="GO"
assert RevalidationPolicy().next("REVISE",0)["revalidate"] is True
assert ValidationState(root).save("v1",{"x":1})["x"]==1
assert ValidationAudit(root).append({"event":"x"})["event"]=="x"
assert BuildPromotionBridge().build(a,{"decision":"GO"})["mission_type"]=="build"
r=CEOValidationRuntimeBridge(root).run(mission); assert r["success"] is True
print(json.dumps({
 "success":True,
 "status":"phase841_856_verification_passed",
 "cycle_status":"phase856_autonomous_validation_decision_engine_ready"
},indent=2))
