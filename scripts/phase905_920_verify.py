#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos_phase905_920 import *

root=Path(tempfile.mkdtemp())
history=[{"confidence":.657},{"confidence":.657}]
validation={"decision":"REVISE","scores":{"problem_evidence":.433,"pricing_validation":.45,"validation_confidence":.657}}
evidence=[{"id":"1","source_class":"public_web","tags":["problem"]}]
c=StagnationRootCause().analyze(history,validation,evidence); assert "confidence_stagnation" in c["reasons"]
assert StrategyReplanner().build(c)["actions"]
q=QueryStrategyMutator().mutate("x",c,1); assert "strategy round 1" in q
assert ProviderMixOptimizer().optimize([],c)
assert EvidenceNoveltyScore().score([{"id":"1"}],[{"id":"2"}])["novelty"]==1.0
assert SourceGapTargeter().missing(evidence)
assert SignalQualityRanker().rank(evidence)
assert ResearchBudgetAllocator().allocate(c)
assert AdaptiveRetryPolicy().decide("a","b",[],["x"],0)["retry"]
assert StrategyState(root).save("x",{"a":1})["a"]==1
assert StrategyAudit(root).append({"event":"x"})["event"]=="x"
assert AntiLoopGuard().evaluate([{"query":"a","providers":["x"]},{"query":"a","providers":["x"]}])["looping"]
assert RuntimeStatus().status()["success"]
print(json.dumps({"success":True,"status":"phase905_920_verification_passed",
"cycle_status":"phase920_adaptive_research_strategy_recovery_ready"},indent=2))
