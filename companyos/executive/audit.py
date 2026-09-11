from datetime import datetime, timezone
from typing import Dict, List
from .models import Venture, Worker


def run_self_audit(ventures: List[Venture], workers: List[Worker], capital_report: Dict, dependency_report: Dict) -> Dict:
    issues: List[Dict] = []

    venture_ids = [v.venture_id for v in ventures]
    if len(venture_ids) != len(set(venture_ids)):
        issues.append({"severity": "critical", "code": "duplicate_venture_id"})

    worker_ids = [w.worker_id for w in workers]
    if len(worker_ids) != len(set(worker_ids)):
        issues.append({"severity": "critical", "code": "duplicate_worker_id"})

    if capital_report.get("deployable", 0) < 0:
        issues.append({"severity": "critical", "code": "negative_deployable_capital"})

    if dependency_report.get("cycles"):
        issues.append({
            "severity": "high",
            "code": "dependency_cycle",
            "count": len(dependency_report["cycles"]),
        })

    overloaded = [w.worker_id for w in workers if w.current_load > w.capacity]
    if overloaded:
        issues.append({"severity": "high", "code": "worker_overload", "workers": overloaded})

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "passed": not any(i["severity"] == "critical" for i in issues),
        "issues": issues,
        "venture_count": len(ventures),
        "worker_count": len(workers),
    }
