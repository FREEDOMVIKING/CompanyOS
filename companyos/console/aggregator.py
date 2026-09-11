from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
import os

from .storage import read_json, read_jsonl

class ConsoleAggregator:
    def __init__(self, home: Path | None = None):
        self.home = Path(home or os.environ.get("COMPANYOS_HOME", str(Path.home() / "companyos")))
        self.runtime = self.home / "companyos_runtime"

    def snapshot(self) -> Dict:
        executive_dir = self.runtime / "phase18201_18300"
        control_dir = self.runtime / "controlplane"

        dashboard = read_json(executive_dir / "executive_dashboard.json", {})
        services = read_json(control_dir / "services.json", {"services": {}})
        health = read_json(control_dir / "system_health.json", {})
        events = read_json(executive_dir / "executive_events.json", [])
        decisions = read_json(executive_dir / "latest_executive_decisions.json", [])
        ranking = read_json(executive_dir / "latest_priority_ranking.json", [])
        capital = read_json(executive_dir / "latest_capital_proposals.json", {})
        workforce = read_json(executive_dir / "latest_workforce_plan.json", {})
        audit = read_json(executive_dir / "latest_self_audit.json", {})
        memory = read_json(executive_dir / "ceo_memory_compressed.json", {})
        ventures = read_json(executive_dir / "ventures.json", [])
        workers = read_json(executive_dir / "workers.json", [])
        finance = read_json(executive_dir / "finance_state.json", {"available_capital": 0.0})

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "phase": "18401-18500",
            "health": health,
            "services": services.get("services", {}),
            "ventures": self._venture_pipeline(ventures, ranking, decisions),
            "workers": self._worker_view(workers, workforce),
            "tasks": self._task_view(decisions),
            "decisions": decisions[-100:],
            "capital": capital,
            "finance": self._finance_summary(finance, capital, dashboard),
            "events": list(reversed(events[-200:])),
            "audit": audit,
            "memory": memory,
            "executive": dashboard,
        }

    def _venture_pipeline(self, ventures: List[Dict], ranking: List[Dict], decisions: List[Dict]) -> List[Dict]:
        rank_map = {x.get("venture_id"): x for x in ranking}
        decision_map = {x.get("venture_id"): x for x in decisions}
        output = []
        for venture in ventures:
            vid = venture.get("venture_id")
            output.append({
                **venture,
                "priority_score": rank_map.get(vid, {}).get("score", 0),
                "scale_action": decision_map.get(vid, {}).get("scale_action"),
                "capital_proposed": decision_map.get(vid, {}).get("capital_proposed", 0),
                "workers_proposed": decision_map.get(vid, {}).get("workers_proposed", []),
            })
        return sorted(output, key=lambda x: x.get("priority_score", 0), reverse=True)

    def _worker_view(self, workers: List[Dict], workforce: Dict) -> List[Dict]:
        reverse = {}
        for venture_id, worker_ids in workforce.items():
            for worker_id in worker_ids:
                reverse.setdefault(worker_id, []).append(venture_id)
        return [{**w, "assigned_ventures": reverse.get(w.get("worker_id"), [])} for w in workers]

    def _task_view(self, decisions: List[Dict]) -> List[Dict]:
        tasks = []
        for d in decisions:
            action = d.get("scale_action")
            if action:
                tasks.append({
                    "task_id": f"{d.get('venture_id')}:{action}",
                    "venture_id": d.get("venture_id"),
                    "action": action,
                    "status": "proposed",
                    "approval_required": d.get("approval_required", False),
                    "priority_score": d.get("priority_score", 0),
                })
        return sorted(tasks, key=lambda x: x["priority_score"], reverse=True)

    def _finance_summary(self, finance: Dict, capital: Dict, dashboard: Dict) -> Dict:
        allocations = capital.get("allocations", {})
        proposed = sum(float(x.get("proposed", 0) or 0) for x in allocations.values())
        return {
            "available_capital": float(finance.get("available_capital", 0) or 0),
            "reserve": float(capital.get("reserve", 0) or 0),
            "deployable": float(capital.get("deployable", 0) or 0),
            "proposed_total": round(proposed, 2),
            "execution_mode": dashboard.get("safety", {}).get("financial_execution", "unknown"),
        }
