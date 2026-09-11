from typing import Dict, List

DEFAULT_POOLS = {
    "research": ["market_research", "competitive_analysis", "source_validation"],
    "engineering": ["software_build", "automation", "testing", "deployment"],
    "marketing": ["copywriting", "seo", "campaigns", "analytics"],
    "finance": ["budgeting", "forecasting", "unit_economics", "risk"],
    "operations": ["process_design", "support", "vendor_management", "quality"],
    "legal_review": ["policy_review", "contract_review", "compliance_triage"],
}

def build_agent_registry(workers: List[Dict]) -> Dict:
    registry = {}
    for worker in workers:
        wid = str(worker.get("worker_id", "unknown"))
        specialty = str(worker.get("specialty", "general")).lower()
        pool = _pool_for_specialty(specialty)
        registry[wid] = {
            **worker,
            "pool": pool,
            "skills": DEFAULT_POOLS.get(pool, ["general_execution"]),
            "available_capacity": max(
                0.0,
                float(worker.get("capacity", 1.0)) - float(worker.get("current_load", 0.0)),
            ),
        }
    return registry

def route_tasks(tasks: List[Dict], registry: Dict) -> List[Dict]:
    routed = []
    usage = {wid: float(agent.get("current_load", 0.0)) for wid, agent in registry.items()}
    for task in sorted(tasks, key=lambda x: float(x.get("priority_score", 0)), reverse=True):
        desired = _pool_for_action(str(task.get("action", "")))
        candidates = [
            (wid, agent) for wid, agent in registry.items()
            if agent.get("pool") == desired and usage[wid] < float(agent.get("capacity", 1.0))
        ]
        if not candidates:
            candidates = [
                (wid, agent) for wid, agent in registry.items()
                if usage[wid] < float(agent.get("capacity", 1.0))
            ]
        selected = None
        if candidates:
            selected = max(
                candidates,
                key=lambda pair: (
                    float(pair[1].get("reliability", 0.5)),
                    float(pair[1].get("capacity", 1.0)) - usage[pair[0]],
                ),
            )[0]
            usage[selected] += 0.25
        routed.append({
            **task,
            "desired_pool": desired,
            "assigned_agent": selected,
            "routing_status": "assigned" if selected else "queued_no_capacity",
        })
    return routed

def _pool_for_specialty(specialty: str) -> str:
    for pool in DEFAULT_POOLS:
        if pool in specialty:
            return pool
    if any(x in specialty for x in ["code", "developer", "engineer", "software"]):
        return "engineering"
    if any(x in specialty for x in ["sales", "growth", "brand", "seo"]):
        return "marketing"
    if any(x in specialty for x in ["money", "account", "budget"]):
        return "finance"
    if any(x in specialty for x in ["research", "analyst"]):
        return "research"
    return "operations"

def _pool_for_action(action: str) -> str:
    action = action.lower()
    if any(x in action for x in ["build", "deploy", "test", "technical"]):
        return "engineering"
    if any(x in action for x in ["market", "campaign", "growth", "launch"]):
        return "marketing"
    if any(x in action for x in ["budget", "capital", "finance", "reduce_exposure"]):
        return "finance"
    if any(x in action for x in ["research", "validate", "discover"]):
        return "research"
    return "operations"
