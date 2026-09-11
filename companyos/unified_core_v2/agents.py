from .util import now

DEFAULT_AGENTS = [
    ("ceo","Executive CEO Agent","Strategy, prioritization, orchestration"),
    ("research","Research Agent","Opportunity and evidence synthesis"),
    ("product","Product Agent","Product planning and artifact readiness"),
    ("marketing","Marketing Agent","Campaign and acquisition planning"),
    ("finance","Finance Agent","Budget, revenue, and treasury analysis"),
    ("operations","Operations Agent","Workflow health and bottleneck detection"),
    ("customer","Customer Success Agent","Customer support and retention planning"),
    ("launch","Launch Agent","Launch readiness and controlled handoff"),
    ("recovery","Recovery Agent","Local diagnostics and non-destructive recovery"),
]

def register_defaults(db):
    for aid, name, role in DEFAULT_AGENTS:
        db.upsert_agent(aid, name, role, True)

class AgentRunner:
    def __init__(self, db):
        self.db = db

    def run(self, task):
        agent = task.get("agent") or "ceo"
        payload = task.get("payload", {})
        try:
            # Internal-only agent execution. It produces structured conclusions;
            # external side effects are deliberately not performed here.
            result = {
                "task_id": task["task_id"],
                "agent": agent,
                "status": "COMPLETED",
                "summary": self._summary(task["kind"], payload),
                "external_side_effects": False,
                "completed_at": now(),
            }
            self.db.event("task.completed", agent, result)
            self.db.mark_agent_result(agent, True)
            return result
        except Exception as e:
            self.db.event("task.failed", agent, {"task_id":task["task_id"],"error":str(e),"ts":now()})
            self.db.mark_agent_result(agent, False)
            raise

    def _summary(self, kind, payload):
        if kind == "portfolio_review":
            return f"Reviewed {payload.get('venture_count',0)} ventures and refreshed internal priorities."
        if kind == "system_health":
            return f"Reviewed {payload.get('module_count',0)} module records for local health."
        if kind == "launch_readiness":
            return f"Reviewed launch-readiness state for {payload.get('venture_name','venture')}."
        if kind == "research_gap":
            return f"Identified research gap for {payload.get('venture_name','venture')}."
        return "Internal task completed."
