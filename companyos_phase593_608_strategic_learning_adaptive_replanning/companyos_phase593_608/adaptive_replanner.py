from .lesson_extractor import LessonExtractor
from .hypothesis_updater import HypothesisUpdater
from .strategy_adjuster import StrategyAdjuster
from .mission_rewriter import MissionRewriter
from .confidence_updater import ConfidenceUpdater

class AdaptiveReplanner:
    """605: outcome -> lessons -> hypotheses -> strategy -> rewritten mission."""

    def replan(self, before_stage, after_stage, outcome, hypotheses, strategy, next_mission, confidence=0.5):
        lessons = LessonExtractor().extract(before_stage, outcome, after_stage)
        new_hypotheses = HypothesisUpdater().update(hypotheses, lessons)
        new_strategy = StrategyAdjuster().adjust(strategy, lessons)
        rewritten = MissionRewriter().rewrite(next_mission, new_strategy)
        new_confidence = ConfidenceUpdater().update(confidence, lessons)
        return {
            "lessons":lessons,
            "hypotheses":new_hypotheses,
            "strategy":new_strategy,
            "rewritten_mission":rewritten,
            "confidence":new_confidence,
        }
