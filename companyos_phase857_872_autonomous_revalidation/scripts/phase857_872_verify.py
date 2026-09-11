#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos_phase857_872 import *
root=Path(tempfile.mkdtemp())
validation={"decision":"REVISE","scores":{"problem_evidence":0.4,"pricing_validation":0.388,"validation_confidence":0.635},
"contradictions":{"topics":[],"resolved":True},"revalidation":{"next_attempt":1}}
mission={"mission_id":"validation_1","attempts":0,"context":{"venture_id":"v1"}}
g=ValidationGapAnalyzer().analyze(validation); assert len(g)>=2
p=EvidenceAcquisitionPlanner().plan(g); assert p
assert HypothesisResearchTasks().build(p)
assert PricingEvidenceRecovery().task()["dimension"]=="pricing_validation"
assert DemandEvidenceRecovery().task()["dimension"]=="demand"
assert ProblemEvidenceRecovery().task()["dimension"]=="problem_evidence"
assert ProviderRevalidationRouter().route({"x":1})["fallback_enabled"]
assert len(EvidenceMerger().merge([{"id":"1"}],[{"id":"1"},{"id":"2"}]))==2
assert ConfidenceDeltaTracker().calculate(.5,.6)["improved"]
assert not StagnationDetector().evaluate([{"delta":.1},{"delta":.1}])["stagnant"]
assert BoundedRevalidationLoop().evaluate(1,"REVISE",False)["continue"]
r=CEORevalidationRuntimeBridge(root).run(mission,validation); assert r["success"] and r["revalidation_mission"]["mission_type"]=="research"
print(json.dumps({"success":True,"status":"phase857_872_verification_passed",
"cycle_status":"phase872_autonomous_revalidation_evidence_acquisition_ready"},indent=2))
