from .util import stable_id

class TeamBalancer:
    def __init__(self,db):
        self.db=db

    def plan(self):
        companies=self.db.list_companies()
        agents=self.db.list_agents()
        if len(companies)<2 or not agents:
            return 0
        top=max(companies,key=lambda c:float(c.get("priority",0) or 0))
        low=min(companies,key=lambda c:float(c.get("priority",0) or 0))
        candidates=[a for a in agents if a.get("company_id")==low["company_id"] and float(a.get("score",0) or 0)>=90]
        created=0
        for a in candidates[:4]:
            rid=stable_id("reassign",a["agent_id"],top["company_id"])
            self.db.upsert_reassignment(
                rid,a["agent_id"],low["company_id"],top["company_id"],
                "High-performing agent can temporarily support the highest-priority company.",
                "PROPOSED_INTERNAL_ONLY",
                {"live_agent_assignment_changed":False}
            )
            created+=1
        return created
