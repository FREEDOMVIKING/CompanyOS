from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from .storage import append_json, read_json

def generate_notifications(snapshot: Dict) -> List[Dict]:
    notices = []
    now = datetime.now(timezone.utc).isoformat()

    health = snapshot.get("health", {})
    if health and not health.get("overall_healthy", False):
        notices.append(_notice(now, "critical", "system_health", "One or more CompanyOS services require attention."))

    audit = snapshot.get("audit", {})
    if audit and not audit.get("passed", False):
        notices.append(_notice(now, "high", "audit", "The latest executive self-audit requires review."))

    for alert in snapshot.get("bottlenecks", [])[:10]:
        notices.append(_notice(
            now,
            "high" if alert.get("severity", 0) >= 0.7 else "medium",
            "venture_bottleneck",
            f"{alert.get('venture_name') or alert.get('venture_id')} has predicted bottlenecks.",
            alert,
        ))

    unassigned = [t for t in snapshot.get("routed_tasks", []) if t.get("routing_status") != "assigned"]
    if unassigned:
        notices.append(_notice(
            now, "medium", "agent_capacity",
            f"{len(unassigned)} task(s) are waiting for agent capacity.",
            {"task_ids": [t.get("task_id") for t in unassigned[:25]]},
        ))

    return notices

def persist_notifications(path: Path, notices: List[Dict]) -> List[Dict]:
    existing = read_json(path, [])
    fingerprints = {n.get("fingerprint") for n in existing[-500:]}
    for notice in notices:
        if notice["fingerprint"] not in fingerprints:
            append_json(path, notice, limit=2000)
            fingerprints.add(notice["fingerprint"])
    return read_json(path, [])[-500:]

def _notice(timestamp: str, severity: str, category: str, message: str, details=None) -> Dict:
    fingerprint = f"{category}:{message}"
    return {
        "timestamp": timestamp,
        "severity": severity,
        "category": category,
        "message": message,
        "details": details or {},
        "fingerprint": fingerprint,
        "acknowledged": False,
    }
