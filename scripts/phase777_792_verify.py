#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos_phase777_792 import *

root=Path(tempfile.mkdtemp(prefix="phase792_"))
assert ProviderAdapter().execute("x",{},{"provider_results":{"x":{"success":True,"items":[1]}}})["success"]
assert ProviderDispatcher().dispatch("x",{},{"provider_results":{"x":{"success":True,"items":[]}}})["success"]
assert QueryTransformer().transform("abc","github")["type"]=="issues_code_repos"
chain=FallbackChain().build("github","market",[])
assert chain and chain[0]=="github"
batch=EvidenceCollector().collect("public_web","q",{"provider_results":{"public_web":{"success":True,"items":[{"url":"x"}]}}})
assert batch["items"][0]["provider"]=="public_web"
assert len(EvidenceMerger().merge([batch,batch]))==1
assert ProviderErrorNormalizer().normalize({"success":False,"error":"HTTP Error 403: rate limit exceeded"})["kind"]=="rate_limited"
assert FailoverSequencer().next(0,["a","b"],{"retryable":True},0)["continue"]
assert SourceQuota().apply([{"provider":"a"}]*7,5)["dropped"]
assert DiversityGate().evaluate([{"source_class":"a"},{"source_class":"b"}])["passed"]
assert CompletionPolicy().decide(0.8,True,True)["complete"]
assert PartialResultStore(root).save("m1",[{"x":1}])["evidence_count"]==1
assert ProviderExecutionAudit(root).append({"mission_id":"m1"})["mission_id"]=="m1"
packet=ResearchPacketAssembler().assemble(
 [{"name":"public_web","availability":1.0}],
 [{"id":"1","source_class":"official","tags":["problem","demand","alternatives","pricing","risk"]}],
 []
)
assert "summary" in packet
assert "validation_candidate_ready" in LifecycleEvidenceOutput().build(packet)

context={
 "provider_results":{
  "github":{"success":False,"error":"HTTP Error 403: rate limit exceeded","items":[]},
  "public_web":{"success":True,"items":[
   {"url":"a","source_class":"official","tags":["problem","risk"]},
   {"url":"b","source_class":"reputable_news","tags":["demand","alternatives"]},
   {"url":"c","source_class":"competitor_site","tags":["pricing"]},
  ]},
 }
}
result=CEOMultiProviderBridge(root).execute(
 {"mission_id":"m2"},"q","market","github",
 [{"name":"github","availability":0.1},{"name":"public_web","availability":1.0}],
 context
)
assert result["success"]
assert result["execution"][0]["provider"]=="github"
print(json.dumps({
 "success":True,
 "status":"phase777_792_verification_passed",
 "cycle_status":"phase792_multi_provider_research_execution_ready"
},indent=2))
