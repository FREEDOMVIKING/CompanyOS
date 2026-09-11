#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos_phase921_936 import *

root=Path(tempfile.mkdtemp())
assert NovelEvidenceFilter().apply([{"id":"1"}],[{"id":"2"}])["novelty"]==1.0
assert SignalQualityFilter().apply([{"source_class":"official","tags":["problem"]}])["kept"]
assert AdaptiveEvidenceStore(root).save("x",1,[{"id":"1"}])["count"]==1
assert ConfidenceImprovementGate().evaluate(.6,.63)["improved"] is True
assert AdaptiveRoundDecision().decide({"decision":"GO","scores":{"validation_confidence":.8}},{"improved":True},1,1)["action"]=="build"
assert DiminishingReturnGuard().evaluate([{"confidence_delta":0,"novelty":0},{"confidence_delta":0,"novelty":0}])["stop"]
assert StrategyExecutionState(root).save("x",{"a":1})["a"]==1
assert StrategyExecutionAudit(root).append({"event":"x"})["event"]=="x"
assert RuntimeStatus().status()["success"]
print(json.dumps({"success":True,"status":"phase921_936_verification_passed",
"cycle_status":"phase936_adaptive_strategy_execution_feedback_ready"},indent=2))
