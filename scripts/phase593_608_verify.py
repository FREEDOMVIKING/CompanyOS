#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos_phase593_608 import (
    LessonExtractor,HypothesisStore,HypothesisUpdater,StrategyState,StrategyAdjuster,
    MissionRewriter,ExperimentMemory,FailurePattern,SuccessPattern,PortfolioLearning,
    ConfidenceUpdater,LearningAudit,AdaptiveReplanner,CEOLearningBridge,
    LearningHealth,LearningRuntime
)

lessons = LessonExtractor().extract(
    "operations",
    {"activation_rate":0.05,"retention_rate":0.03,"revenue_signal":0.0},
    "operations"
)
assert "weak_activation" in lessons
assert "weak_retention" in lessons

root = Path(tempfile.mkdtemp(prefix="phase608_"))
hs = HypothesisStore(root)
hs.put("v1",{"customer_problem_valid":True})
assert hs.get("v1")["customer_problem_valid"] is True

updated = HypothesisUpdater().update({}, lessons)
assert updated["solution_value_valid"] is False

ss = StrategyState(root)
ss.put("v1",{"focus":"x"})
assert ss.load()["v1"]["focus"] == "x"

strategy = StrategyAdjuster().adjust({}, lessons)
assert "improve_onboarding_and_time_to_value" in strategy["changes"]

rewritten = MissionRewriter().rewrite(
    {"mission_type":"operations","priority":0.5,"context":{}},
    strategy
)
assert rewritten["mission_type"] in ("operations","research","validation","build")

assert ExperimentMemory(root).append("v1","x",{"ok":True})["venture_id"]=="v1"
assert FailurePattern().detect([["weak_activation"],["weak_activation"]])[0]["count"]==2
assert SuccessPattern().detect([["stage_advanced:a->b"],["stage_advanced:a->b"]])[0]["count"]==2
assert PortfolioLearning().summarize([{"venture_id":"v1","last_outcome_score":5,"stagnant_cycles":0}])["progressing_ventures"]==["v1"]
assert ConfidenceUpdater().update(0.5,["weak_activation"]) < 0.5
assert LearningAudit(root).append("v1",lessons,strategy,rewritten)["venture_id"]=="v1"

replan = AdaptiveReplanner().replan(
    "operations","operations",
    {"activation_rate":0.05,"retention_rate":0.03,"revenue_signal":0.0},
    {},{},{"mission_type":"operations","priority":0.5,"context":{}},0.5
)
assert replan["lessons"]

bridge = CEOLearningBridge(root)
applied = bridge.apply(
    "v2","validation","build",
    {"mission_success":True},
    {"mission_type":"build","priority":0.9,"context":{}},
    0.5
)
assert applied["confidence"] > 0.5
assert LearningHealth().evaluate(applied)["healthy"] is True
assert LearningRuntime().status()["success"] is True

print(json.dumps({
    "success":True,
    "status":"phase593_608_verification_passed",
    "cycle_status":"phase608_strategic_learning_adaptive_replanning_ready",
    "lesson_extraction":True,
    "hypothesis_updates":True,
    "strategy_adjustment":True,
    "mission_rewriting":True,
    "experiment_memory":True,
    "failure_patterns":True,
    "success_patterns":True,
    "portfolio_learning":True,
    "confidence_updates":True,
    "learning_audit":True,
    "adaptive_replanner":True,
    "autonomy_mode":"high"
}, indent=2))
