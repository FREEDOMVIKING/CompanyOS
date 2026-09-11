#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos_phase825_840 import *

assert FailureClassifier().classify({"success":False,"error":"HTTP Error 403: rate limit exceeded"})["kind"]=="rate_limited"
assert ProviderEscalationPolicy().decide({"kind":"rate_limited"},1,1)=="switch_provider"
assert "customer demand proof" in QueryReformulator().reformulate("x",["demand"],1)
assert EvidenceGapAnalyzer().analyze([{"tags":["problem"]}])["complete"] is False
assert ProviderRetryBudget().remaining("github",1)==1
assert AdaptiveBackoff().seconds("rate_limited",1)==120

root=Path(tempfile.mkdtemp(prefix="phase840_"))
assert EscalationState(root).update("m1",status="x")["status"]=="x"
assert ProviderChainBuilder().build("github","market")
merged=EvidenceAccumulator().merge([], [{"id":"1","source_class":"official","tags":["problem"]}])
assert merged
assert "delta" in ConfidenceProgress().evaluate([], merged)

threshold=PromotionThreshold().evaluate([
    {"id":"1","source_class":"official","tags":["problem","risk"],"evidence_score":0.9},
    {"id":"2","source_class":"reputable_news","tags":["demand","alternatives"],"evidence_score":0.8},
    {"id":"3","source_class":"competitor_site","tags":["pricing"],"evidence_score":0.75},
])
assert "passed" in threshold

assert DeferredRecoveryPolicy().build({"attempts":0,"context":{}},60,"x")["status"]=="deferred"
assert ResearchEscalationAudit(root).append({"mission_id":"m1"})["mission_id"]=="m1"

mission={
    "mission_id":"m2",
    "mission_type":"research",
    "context":{"query":"test demand","query_type":"market","provider_hint":"github","evidence":[]}
}
provider_results={
    "github":{"success":False,"error":"HTTP Error 403: rate limit exceeded","items":[]},
    "public_web":{"success":True,"items":[
        {"url":"a","source_class":"official","tags":["problem","risk"]},
        {"url":"b","source_class":"reputable_news","tags":["demand","alternatives"]},
        {"url":"c","source_class":"competitor_site","tags":["pricing"]},
    ]},
}
result=CEOResearchEscalationBridge(root).run(mission,provider_results,max_total_attempts=6)
assert result["success"] is True
assert RuntimeStatus().status()["success"] is True

print(json.dumps({
    "success":True,
    "status":"phase825_840_verification_passed",
    "cycle_status":"phase840_research_escalation_provider_recovery_ready"
},indent=2))
