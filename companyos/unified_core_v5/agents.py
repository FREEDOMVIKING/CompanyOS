AGENTS=[
("ceo","Executive CEO Agent","Portfolio strategy and executive orchestration"),
("planner","Planning Agent","Dependency-aware planning"),
("critic","Executive Critic Agent","Plan critique and risk review"),
("research","Research Agent","Opportunity and evidence work"),
("product","Product Agent","Offer and product development"),
("marketing","Marketing Agent","Acquisition and messaging"),
("finance","Finance Agent","Economics and forecasting"),
("operations","Operations Agent","Workflow execution"),
("customer","Customer Success Agent","Support and retention"),
("launch","Launch Agent","Launch readiness"),
("recovery","Recovery Agent","Diagnostics and recovery"),
("analyst","Business Analyst Agent","KPI and performance analysis"),
]

def register(db):
    for aid,n,r in AGENTS:
        db.upsert_agent(aid,n,r,True)
