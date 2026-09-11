from typing import Dict, List
from .models import Venture


def detect_failure_cascades(ventures: List[Venture], dependency_report: Dict) -> List[Dict]:
    by_id = {v.venture_id: v for v in ventures}
    dependents: Dict[str, List[str]] = {}
    for venture_id, deps in dependency_report.get("graph", {}).items():
        for dependency in deps:
            dependents.setdefault(dependency, []).append(venture_id)

    alerts = []
    for venture in ventures:
        downstream = dependents.get(venture.venture_id, [])
        severity = venture.failure_probability * (1 + len(downstream))
        if severity >= 0.80:
            alerts.append({
                "source_venture": venture.venture_id,
                "downstream_ventures": downstream,
                "severity": round(severity, 4),
                "recommended_action": "isolate_dependency_and_create_fallback",
            })
    return sorted(alerts, key=lambda x: x["severity"], reverse=True)
