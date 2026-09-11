from .evidence_updater import EvidenceUpdater
from .outcome_ingestor import OutcomeIngestor
from .stage_advancer import StageAdvancer
from .next_action_policy import NextActionPolicy
from .mission_factory import MissionFactory
from .outcome_score import OutcomeScore
from .progress_guard import ProgressGuard

class VentureFeedbackLoop:
    """587: one closed-loop venture update."""

    def update(self, record, outcome):
        record = dict(record or {})
        before_stage = record.get("stage","research")
        normalized = OutcomeIngestor().ingest(outcome)
        evidence = EvidenceUpdater().merge(record.get("evidence"), normalized)
        after_stage = StageAdvancer().next_stage(before_stage, evidence)
        score = OutcomeScore().score(before_stage, after_stage, evidence)

        record["stage"] = after_stage
        record["evidence"] = evidence
        record["last_outcome_score"] = score

        guard = ProgressGuard().evaluate(record)
        record["stagnant_cycles"] = guard["stagnant_cycles"]
        record["progress_guard_action"] = guard["action"]

        next_action = NextActionPolicy().decide(after_stage, evidence)
        if guard["action"] == "pause_and_research":
            next_action = "collect_targeted_evidence"

        mission = MissionFactory().build(
            record.get("venture_id"),
            next_action,
            {"venture_record":record},
        )

        return {
            "record":record,
            "before_stage":before_stage,
            "after_stage":after_stage,
            "next_action":next_action,
            "next_mission":mission,
            "outcome_score":score,
        }
