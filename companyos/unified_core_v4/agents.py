AGENTS=[
("ceo","Executive CEO Agent","Long-horizon strategy and orchestration"),
("research","Research Agent","Opportunity discovery and evidence"),
("product","Product Agent","Offer and product development"),
("marketing","Marketing Agent","Acquisition and messaging"),
("finance","Finance Agent","Economics and resource analysis"),
("operations","Operations Agent","Execution and workflow health"),
("customer","Customer Success Agent","Support and retention"),
("launch","Launch Agent","Validation and launch readiness"),
("recovery","Recovery Agent","Diagnostics and recovery"),
("critic","Executive Critic Agent","Challenges plans and identifies weaknesses"),
("planner","Planning Agent","Builds dependency-aware execution plans"),
]

def register(db):
    for a,n,r in AGENTS: db.upsert_agent(a,n,r,True)
