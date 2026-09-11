from typing import Dict, List

def trend_summary(history: List[Dict]) -> Dict:
    if not history:
        return {"points":0,"venture_health_trend":"flat","assignment_trend":"flat"}
    recent = history[-20:]
    return {
        "points": len(recent),
        "venture_health_trend": _trend([float(x.get("average_venture_health",0)) for x in recent]),
        "assignment_trend": _trend([float(x.get("task_assignment_rate",0)) for x in recent]),
        "latest": recent[-1],
    }

def _trend(values):
    if len(values) < 2:
        return "flat"
    delta = values[-1] - values[0]
    if delta > 0.02: return "up"
    if delta < -0.02: return "down"
    return "flat"
