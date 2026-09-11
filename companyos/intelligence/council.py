from typing import Dict, List

DIRECTORS=("research","engineering","finance","marketing","operations")

def executive_council(ventures: List[Dict], bottlenecks: List[Dict], finance: Dict) -> List[Dict]:
    recs=[]
    for director in DIRECTORS:
        recs.append(_recommend(director,ventures,bottlenecks,finance))
    return recs

def _recommend(director,ventures,bottlenecks,finance):
    if director=="research":
        action="validate_highest_ranked_opportunity"
        reason="Prioritize evidence quality before increasing commitment."
    elif director=="engineering":
        action="focus_build_capacity_on_ready_workflows"
        reason="Reduce work in progress and unblock dependency chains."
    elif director=="finance":
        deployable=float(finance.get("deployable",0) or 0)
        action="preserve_reserve" if deployable <= 0 else "fund_high_confidence_milestones"
        reason="Protect liquidity while financing measurable milestones."
    elif director=="marketing":
        action="prepare_demand_tests_for_launch_ready_ventures"
        reason="Use controlled acquisition tests before scaling spend."
    else:
        action="rebalance_agents_around_bottlenecks"
        reason=f"{len(bottlenecks)} predicted bottleneck(s) require operational attention."
    return {
        "director":director,
        "action":action,
        "reason":reason,
        "priority":"high" if bottlenecks else "normal",
    }
