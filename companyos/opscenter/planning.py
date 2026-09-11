from datetime import datetime, timedelta, timezone
from typing import Dict, List

STAGE_MILESTONES = {
    "discovery": ["Define opportunity thesis", "Collect market evidence", "Select validation test"],
    "validation": ["Run demand test", "Review unit economics", "Approve build decision"],
    "build": ["Complete minimum viable product", "Pass quality gate", "Prepare launch assets"],
    "launch": ["Launch controlled release", "Measure acquisition", "Resolve launch blockers"],
    "operations": ["Stabilize delivery", "Improve retention", "Document operating process"],
    "scale": ["Expand capacity", "Optimize acquisition", "Protect service quality"],
}

def build_roadmap(ventures: List[Dict], horizon_weeks: int = 8) -> List[Dict]:
    now = datetime.now(timezone.utc)
    roadmap = []
    for venture in ventures:
        milestones = STAGE_MILESTONES.get(str(venture.get("stage", "discovery")), STAGE_MILESTONES["discovery"])
        progress = float(venture.get("progress", 0.0) or 0.0)
        priority = float(venture.get("priority_score", 0.0) or 0.0)
        for index, milestone in enumerate(milestones):
            week = min(horizon_weeks, max(1, index + 1 + int((1.0 - progress) * 2)))
            due = now + timedelta(weeks=week)
            roadmap.append({
                "venture_id": venture.get("venture_id"),
                "venture_name": venture.get("name"),
                "milestone_id": f"{venture.get('venture_id')}:{index+1}",
                "milestone": milestone,
                "week": week,
                "due_at": due.isoformat(),
                "priority_score": priority,
                "status": "planned",
            })
    return sorted(roadmap, key=lambda x: (x["week"], -x["priority_score"]))

def forecast_bottlenecks(ventures: List[Dict], roadmap: List[Dict], routed_tasks: List[Dict]) -> List[Dict]:
    alerts = []
    tasks_by_venture = {}
    for task in routed_tasks:
        tasks_by_venture.setdefault(task.get("venture_id"), []).append(task)

    for venture in ventures:
        vid = venture.get("venture_id")
        reasons = []
        severity = 0.0
        if venture.get("blocked"):
            reasons.append("venture_marked_blocked")
            severity += 0.5
        if float(venture.get("failure_probability", 0.0) or 0.0) >= 0.5:
            reasons.append("elevated_failure_probability")
            severity += 0.35
        if len(venture.get("dependencies", []) or []) >= 3:
            reasons.append("high_dependency_count")
            severity += 0.2
        if any(t.get("routing_status") != "assigned" for t in tasks_by_venture.get(vid, [])):
            reasons.append("insufficient_agent_capacity")
            severity += 0.3
        if reasons:
            alerts.append({
                "venture_id": vid,
                "venture_name": venture.get("name"),
                "severity": round(min(1.0, severity), 3),
                "reasons": reasons,
                "recommended_action": "rebalance_resources_and_remove_blocker",
            })
    return sorted(alerts, key=lambda x: x["severity"], reverse=True)
