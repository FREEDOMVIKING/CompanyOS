from datetime import datetime, timezone
from typing import Dict

def _num(value, default=0.0):
    return default if value is None else float(value)

def venture_health(venture: Dict) -> float:
    progress = _num(venture.get("progress"), 0.0)
    confidence = _num(venture.get("confidence"), 0.5)
    risk = _num(venture.get("risk"), 0.5)
    failure = _num(venture.get("failure_probability"), 0.0)
    blocked_penalty = 0.35 if venture.get("blocked") else 0.0
    score = 0.35 * progress + 0.35 * confidence + 0.30 * (1.0 - risk)
    score -= 0.35 * failure + blocked_penalty
    return round(max(0.0, min(1.0, score)), 4)

def calculate_kpis(snapshot: Dict) -> Dict:
    ventures = snapshot.get("ventures", [])
    tasks = snapshot.get("routed_tasks", [])
    roadmap = snapshot.get("roadmap", [])
    assigned = sum(1 for t in tasks if t.get("routing_status") == "assigned")
    health_scores = [venture_health(v) for v in ventures]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "venture_count": len(ventures),
        "average_venture_health": round(sum(health_scores) / len(health_scores), 4) if health_scores else 0.0,
        "task_count": len(tasks),
        "task_assignment_rate": round(assigned / len(tasks), 4) if tasks else 1.0,
        "planned_milestone_count": len(roadmap),
        "blocked_venture_count": sum(1 for v in ventures if v.get("blocked")),
        "capital_proposed_total": round(sum(float(v.get("capital_proposed", 0) or 0) for v in ventures), 2),
    }
