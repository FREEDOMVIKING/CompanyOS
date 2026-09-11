from datetime import datetime, timezone
from typing import Dict, List

def strategic_plan(opportunities: List[Dict], council: List[Dict], portfolio: Dict) -> Dict:
    top=opportunities[:3]
    objectives=[]
    for index,item in enumerate(top,1):
        objectives.append({
            "objective_id":f"objective:{index}",
            "venture_id":item.get("venture_id"),
            "title":f"{item.get('recommended_posture')} {item.get('name') or item.get('venture_id')}",
            "priority":index,
            "success_metric":"complete next measurable milestone with audit pass",
        })
    return {
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "planning_horizon_days":90,
        "portfolio_posture":_portfolio_posture(portfolio),
        "objectives":objectives,
        "council_alignment":len({x.get("priority") for x in council}) <= 2,
    }

def _portfolio_posture(portfolio):
    score=float(portfolio.get("score",0) or 0)
    if score>=0.75:return "growth"
    if score>=0.5:return "selective_expansion"
    if score>=0.3:return "stabilization"
    return "recovery"
