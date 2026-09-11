#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos_phase793_808 import *

root = Path(tempfile.mkdtemp(prefix="phase808_"))
mission = {
    "mission_id":"m1",
    "mission_type":"research",
    "priority":0.9,
    "attempts":0,
    "context":{
        "venture_id":"v1",
        "query_type":"market",
        "query":"test demand",
        "provider_hint":"github",
        "provider_results":{
            "github":{"success":False,"error":"HTTP Error 403: rate limit exceeded","items":[]},
            "public_web":{"success":True,"items":[
                {"url":"a","source_class":"official","tags":["problem","risk"]},
                {"url":"b","source_class":"reputable_news","tags":["demand","alternatives"]},
                {"url":"c","source_class":"competitor_site","tags":["pricing"]},
            ]},
        },
    },
}

ctx = ResearchExecutionContext().build(mission)
assert ctx["venture_id"] == "v1"
assert ProviderResultBridge().build(mission)["provider_results"]["github"]["success"] is False

result = MultiProviderRuntimeAdapter(root).execute(mission, {})
assert result["success"] is True

gate = QualityHandoffGate().evaluate(result)
assert "passed" in gate

handoff = ValidationHandoff().build(mission, result)
assert handoff["mission_type"] == "validation"

assert ResearchNextAction().decide({"passed":True}, result) == "handoff_to_validation"
assert DeferredMissionPolicy().build(mission)["status"] == "deferred"
assert ProviderChainState(root).save("m1", result)["provider_chain"]
assert ResearchExecutionAudit(root).append("x", {})["event"] == "x"
assert RuntimeResearchGuard().should_run(mission) is True

cycle = ResearchCycleController(root).run(mission, {})
assert cycle["success"] is True

queue_item = ValidationQueueBridge().build(handoff)
assert queue_item["mission_type"] == "validation"
assert queue_item["mission_id"].endswith("_validation")

assert ResearchRuntimeHealth().evaluate(cycle)["healthy"] is True

integration = ClosedLoopIntegration(root).process(mission, {})
assert integration["handled"] is True

bridge = CEOResearchExecutionBridge(root).process(mission, {})
assert bridge["handled"] is True

assert RuntimeStatus().status()["success"] is True

print(json.dumps({
    "success":True,
    "status":"phase793_808_verification_passed",
    "cycle_status":"phase808_live_research_execution_validation_handoff_ready"
}, indent=2))
