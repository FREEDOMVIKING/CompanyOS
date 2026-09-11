#!/usr/bin/env python3
import json
from companyos_phase745_760 import *
assert ProviderHealth().score({"availability":1.0,"recent_failures":0})==10.0
sel=ProviderSelector().choose([{"name":"a","availability":0.5},{"name":"b","availability":1.0}])
assert sel["selected"]["name"]=="b"
assert SourceDiversifier().evaluate([{"source_class":"official"},{"source_class":"reputable_news"}])["diversified"]
assert QueryRouter().route("technical")[0]=="github"
assert len(DedupeEvidence().dedupe([{"url":"x"},{"url":"x"}]))==1
assert 0 <= FreshnessScore().score({}) <= 1
assert CredibilityScore().score({"source_class":"official"})==1.0
comp=EvidenceCompleteness().evaluate([{"tags":["problem","demand","alternatives","pricing","risk"]}])
assert comp["complete"]
assert ContradictionDetector().detect([{"topic":"x","stance":"positive"},{"topic":"x","stance":"negative"}])["has_contradictions"]
assert WeakSignalFilter().filter([{"evidence_score":0.8},{"evidence_score":0.2}])["kept"]
assert ResearchStopPolicy().decide({"complete":True},0.8,1)["stop"]
assert RetryBudget().remaining("github",1)==1
assert EvidenceConfidence().score([{"evidence_score":0.8},{"evidence_score":0.6}])==0.7
norm=ResearchNormalizer().normalize([{"source_class":"official"}]); assert "evidence_score" in norm[0]
packet=ResearchQualityRuntime().run(
 [{"name":"public_web","availability":1.0}],
 [{"id":"1","source_class":"official","tags":["problem","demand","alternatives","pricing","risk"]}],
 []
)
assert packet["success"]
assert CEOResearchSummary().build(packet)["evidence_count"]==1
print(json.dumps({
 "success":True,
 "status":"phase745_760_verification_passed",
 "cycle_status":"phase760_provider_aware_research_quality_ready"
},indent=2))
