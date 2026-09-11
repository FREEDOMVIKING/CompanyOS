#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos_phase761_776 import *
root=Path(tempfile.mkdtemp(prefix="phase776_"))
mission={"mission_id":"m1","mission_type":"research","attempts":0,"context":{"venture_id":"v1","query_type":"market"}}
assert ResearchMissionAdapter().adapt(mission)["venture_id"]=="v1"
providers=[{"name":"github","availability":0.2},{"name":"public_web","availability":1.0}]
sel=ProviderHealthBridge(root).select(providers); assert sel["selected"]["name"]=="public_web"
quality=EvidenceQualityGate().evaluate(
 providers,
 [
  {"id":"1","source_class":"official","tags":["problem","risk"]},
  {"id":"2","source_class":"reputable_news","tags":["demand","alternatives"]},
  {"id":"3","source_class":"competitor_site","tags":["pricing"]},
 ],[]
)
assert "summary" in quality
assert ResearchExecutionPolicy().decide({"passed":True},True,1)=="advance"
assert FallbackCycle().choose("github","market")!="github"
assert ResearchResultAdapter().adapt({"evidence":[{"text":"x"}]},"github")
assert "validation_candidate_ready" in LifecycleEvidenceBridge().build(quality)
assert "evidence_confidence" in LearningEvidenceBridge().build(quality)
assert ResearchRetryState(root).increment("m1","github")==1
assert ResearchAudit(root).append("x",{})["event"]=="x"
result=IntegratedResearchExecutor(root).evaluate_result(
 mission,
 {"success":True,"evidence":[
  {"id":"1","source_class":"official","tags":["problem","demand","alternatives","pricing","risk"]}
 ]},
 providers
)
assert result["success"]
assert ResearchCycleHealth().evaluate(result)["healthy"]
assert ResearchIntegrationRuntime().status()["success"]
assert CEOResearchRuntimeBridge(root).evaluate(mission,{"success":True,"evidence":[]},providers)["success"]
print(json.dumps({
 "success":True,
 "status":"phase761_776_verification_passed",
 "cycle_status":"phase776_ceo_research_runtime_bridge_ready"
},indent=2))
