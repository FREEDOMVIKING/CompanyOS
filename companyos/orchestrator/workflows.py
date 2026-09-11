from datetime import datetime, timezone
from typing import Dict, List

def create_workflows(roadmap: List[Dict], routed_tasks: List[Dict]) -> List[Dict]:
    by_venture = {}
    for m in roadmap:
        by_venture.setdefault(m.get("venture_id"), []).append(m)
    tasks_by_venture = {}
    for t in routed_tasks:
        tasks_by_venture.setdefault(t.get("venture_id"), []).append(t)

    workflows = []
    for venture_id, milestones in by_venture.items():
        milestones = sorted(milestones, key=lambda x: x.get("week", 0))
        steps = []
        previous = None
        for m in milestones:
            sid = f"step:{m.get('milestone_id')}"
            steps.append({
                "step_id": sid,
                "milestone_id": m.get("milestone_id"),
                "name": m.get("milestone"),
                "status": "ready" if previous is None else "waiting",
                "depends_on": [previous] if previous else [],
                "assigned_agent": _agent_for_venture(tasks_by_venture.get(venture_id, [])),
            })
            previous = sid
        workflows.append({
            "workflow_id": f"workflow:{venture_id}",
            "venture_id": venture_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "active" if steps else "empty",
            "steps": steps,
        })
    return workflows

def trigger_ready_steps(workflows: List[Dict]) -> List[Dict]:
    triggered = []
    for wf in workflows:
        completed = {s["step_id"] for s in wf["steps"] if s.get("status") == "completed"}
        for step in wf["steps"]:
            if step.get("status") in {"waiting","ready"} and all(dep in completed for dep in step.get("depends_on", [])):
                step["status"] = "ready"
                triggered.append({
                    "workflow_id": wf["workflow_id"],
                    "venture_id": wf["venture_id"],
                    "step_id": step["step_id"],
                    "action": step["name"],
                    "assigned_agent": step.get("assigned_agent"),
                    "trigger": "dependencies_satisfied",
                })
    return triggered

def detect_deadlocks(workflows: List[Dict]) -> List[Dict]:
    issues = []
    for wf in workflows:
        ids = {s["step_id"] for s in wf["steps"]}
        for step in wf["steps"]:
            missing = [d for d in step.get("depends_on", []) if d not in ids]
            if missing:
                issues.append({"workflow_id":wf["workflow_id"],"step_id":step["step_id"],"missing_dependencies":missing})
    return issues

def _agent_for_venture(tasks):
    for t in tasks:
        if t.get("assigned_agent"):
            return t["assigned_agent"]
    return None
