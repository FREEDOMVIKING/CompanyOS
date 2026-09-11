from typing import Dict, List
from .models import Venture
from .prioritizer import score_venture


def allocate_capital(
    ventures: List[Venture],
    available_capital: float,
    reserve_ratio: float = 0.20,
    single_action_limit: float = 15000.0,
) -> Dict[str, Dict]:
    available_capital = max(0.0, float(available_capital))
    deployable = available_capital * (1.0 - max(0.0, min(0.95, reserve_ratio)))
    positive = [(v, max(0.0, score_venture(v))) for v in ventures if not v.blocked]
    total_score = sum(score for _, score in positive)

    result: Dict[str, Dict] = {}
    for venture, score in positive:
        requested = max(0.0, venture.capital_requested)
        proportional = deployable * (score / total_score) if total_score else 0.0
        proposed = min(requested, proportional, single_action_limit)
        result[venture.venture_id] = {
            "proposed": round(proposed, 2),
            "requested": round(requested, 2),
            "approval_required": proposed > 0.0,
            "execution_status": "proposal_only",
        }

    return {
        "available_capital": round(available_capital, 2),
        "reserve": round(available_capital - deployable, 2),
        "deployable": round(deployable, 2),
        "allocations": result,
    }
