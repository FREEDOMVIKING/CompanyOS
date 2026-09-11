from .business_case import BusinessCase
from .venture_scorecard import VentureScorecard
from .commitment_gate import CommitmentGate
from .launch_readiness import LaunchReadiness
from .kill_scale_policy import KillScalePolicy
from .milestone_engine import MilestoneEngine

class BusinessExecutionManager:
    """573: unified venture execution review."""

    def review(self, venture, evidence):
        stage=venture.get("stage","research")
        scorecard=VentureScorecard().score(evidence)
        gate=CommitmentGate().evaluate(stage,evidence)
        launch=LaunchReadiness().evaluate(evidence) if stage=="launch" else None
        decision=KillScalePolicy().decide({**evidence,**scorecard["dimensions"]})
        return {
            "success":True,
            "status":"business_execution_review_ready",
            "business_case":BusinessCase().build(venture),
            "stage":stage,
            "scorecard":scorecard,
            "commitment_gate":gate,
            "launch_readiness":launch,
            "decision":decision,
            "next_milestone":MilestoneEngine().next(stage),
        }
