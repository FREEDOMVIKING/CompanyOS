from datetime import datetime, timezone
from pathlib import Path
import os

from .storage import read_json
from .agents import build_agent_registry, route_tasks
from .planning import build_roadmap, forecast_bottlenecks
from .analytics import calculate_kpis, venture_health

class OperationsAggregator:
    def __init__(self, home: Path | None = None):
        self.home = Path(home or os.environ.get("COMPANYOS_HOME", str(Path.home() / "companyos")))
        self.runtime = self.home / "companyos_runtime"

    def base_snapshot(self):
        executive_dir = self.runtime / "phase18201_18300"
        control_dir = self.runtime / "controlplane"

        dashboard = read_json(executive_dir / "executive_dashboard.json", {})
        ventures = read_json(executive_dir / "ventures.json", [])
        ranking = read_json(executive_dir / "latest_priority_ranking.json", [])
        decisions = read_json(executive_dir / "latest_executive_decisions.json", [])
        workers = read_json(executive_dir / "workers.json", [])
        workforce = read_json(executive_dir / "latest_workforce_plan.json", {})
        events = read_json(executive_dir / "executive_events.json", [])
        audit = read_json(executive_dir / "latest_self_audit.json", {})
        capital = read_json(executive_dir / "latest_capital_proposals.json", {})
        finance = read_json(executive_dir / "finance_state.json", {"available_capital": 0.0})
        health = read_json(control_dir / "system_health.json", {})
        services = read_json(control_dir / "services.json", {"services": {}}).get("services", {})

        ranking_map = {x.get("venture_id"): x for x in ranking}
        decision_map = {x.get("venture_id"): x for x in decisions}
        merged = []
        for venture in ventures:
            vid = venture.get("venture_id")
            decision = decision_map.get(vid, {})
            merged.append({
                **venture,
                "priority_score": ranking_map.get(vid, {}).get("score", 0),
                "scale_action": decision.get("scale_action"),
                "capital_proposed": decision.get("capital_proposed", 0),
                "workers_proposed": decision.get("workers_proposed", []),
                "health_score": venture_health(venture),
            })

        tasks = []
        for decision in decisions:
            action = decision.get("scale_action")
            if action:
                tasks.append({
                    "task_id": f"{decision.get('venture_id')}:{action}",
                    "venture_id": decision.get("venture_id"),
                    "action": action,
                    "priority_score": decision.get("priority_score", 0),
                    "approval_required": decision.get("approval_required", False),
                    "status": "proposed",
                })

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "phase": "18501-18700",
            "health": health,
            "services": services,
            "ventures": sorted(merged, key=lambda x: x.get("priority_score", 0), reverse=True),
            "workers": workers,
            "workforce": workforce,
            "tasks": tasks,
            "events": list(reversed(events[-300:])),
            "audit": audit,
            "capital": capital,
            "finance_state": finance,
            "executive": dashboard,
        }

    def snapshot(self):
        data = self.base_snapshot()
        registry = build_agent_registry(data["workers"])
        routed = route_tasks(data["tasks"], registry)
        roadmap = build_roadmap(data["ventures"])
        bottlenecks = forecast_bottlenecks(data["ventures"], roadmap, routed)
        data.update({
            "agent_registry": registry,
            "routed_tasks": routed,
            "roadmap": roadmap,
            "bottlenecks": bottlenecks,
        })
        data["kpis"] = calculate_kpis(data)
        return data
