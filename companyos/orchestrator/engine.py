from pathlib import Path
from datetime import datetime, timezone
import os

from .storage import read_json, write_json
from .graph import build_graph
from .workflows import create_workflows, trigger_ready_steps, detect_deadlocks
from .delegation import build_delegations
from .trends import trend_summary

class OrchestratorEngine:
    def __init__(self, home=None):
        self.home = Path(home or os.environ.get("COMPANYOS_HOME", str(Path.home()/"companyos")))
        self.ops = self.home/"companyos_runtime"/"opscenter"
        self.runtime = self.home/"companyos_runtime"/"orchestrator"
        self.runtime.mkdir(parents=True, exist_ok=True)

    def run_cycle(self):
        snapshot = read_json(self.ops/"latest_ops_snapshot.json", {})
        ventures = snapshot.get("ventures", [])
        tasks = snapshot.get("routed_tasks", [])
        agents = snapshot.get("agent_registry", {})
        roadmap = snapshot.get("roadmap", [])
        events = snapshot.get("events", [])
        history = read_json(self.ops/"kpi_history.json", [])

        workflows = create_workflows(roadmap, tasks)
        triggered = trigger_ready_steps(workflows)
        deadlocks = detect_deadlocks(workflows)
        delegations = build_delegations(tasks, agents)
        graph = build_graph(ventures, tasks, agents, roadmap, events)

        result = {
            "phase":"18701-19000",
            "generated_at":datetime.now(timezone.utc).isoformat(),
            "workflows":workflows,
            "triggered_steps":triggered,
            "deadlocks":deadlocks,
            "delegations":delegations,
            "knowledge_graph":graph,
            "trends":trend_summary(history),
            "summary":{
                "workflow_count":len(workflows),
                "delegation_count":len(delegations),
                "triggered_step_count":len(triggered),
                "deadlock_count":len(deadlocks),
                "graph_nodes":graph["node_count"],
                "graph_edges":graph["edge_count"],
            }
        }
        write_json(self.runtime/"latest_orchestration.json", result)
        return result
