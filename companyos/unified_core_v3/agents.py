from .util import now

AGENTS=[
("ceo","Executive CEO","Strategy and cross-agent orchestration"),
("research","Research Agent","Opportunity and evidence research"),
("product","Product Agent","Product planning and packaging"),
("marketing","Marketing Agent","Acquisition and campaign planning"),
("finance","Finance Agent","Budget and revenue analysis"),
("operations","Operations Agent","Operational health"),
("customer","Customer Success Agent","Support and retention"),
("launch","Launch Agent","Launch readiness and handoffs"),
("recovery","Recovery Agent","Diagnostics and local recovery"),
]

def register_agents(db):
    for a,n,r in AGENTS:
        db.upsert_agent(a,n,r,True)

class AgentRunner:
    def __init__(self, db, bus):
        self.db=db
        self.bus=bus

    def run(self, task):
        agent=task.get("agent") or "ceo"
        payload=task.get("payload",{})
        kind=task["kind"]
        if kind=="system_health":
            summary=f"Health review completed for {payload.get('module_count',0)} modules."
        elif kind=="portfolio_review":
            summary=f"Portfolio review completed for {payload.get('venture_count',0)} ventures."
        elif kind=="launch_readiness":
            summary=f"Launch readiness reviewed for {payload.get('venture_name','venture')}."
        elif kind=="plugin_health":
            summary=f"Plugin health reviewed for {payload.get('plugin_count',0)} plugins."
        else:
            summary="Internal task completed."
        result={"task_id":task["task_id"],"agent":agent,"status":"COMPLETED","summary":summary,"external_side_effects":False,"completed_at":now()}
        self.bus.publish("agent.result",agent,result)
        self.db.agent_result(agent,True)
        return result
