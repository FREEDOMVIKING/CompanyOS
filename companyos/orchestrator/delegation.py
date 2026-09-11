from typing import Dict, List

def build_delegations(tasks: List[Dict], agents: Dict) -> List[Dict]:
    delegations = []
    pool_leads = {}
    for aid, agent in agents.items():
        pool = agent.get("pool", "operations")
        current = pool_leads.get(pool)
        if current is None or float(agent.get("reliability",0)) > float(current[1].get("reliability",0)):
            pool_leads[pool] = (aid, agent)

    for task in tasks:
        assigned = task.get("assigned_agent")
        desired = task.get("desired_pool","operations")
        lead = pool_leads.get(desired, (None,None))[0]
        delegations.append({
            "delegation_id": f"delegation:{task.get('task_id')}",
            "task_id": task.get("task_id"),
            "venture_id": task.get("venture_id"),
            "from_agent": lead,
            "to_agent": assigned,
            "pool": desired,
            "status": "delegated" if assigned else "waiting_for_capacity",
        })
    return delegations
