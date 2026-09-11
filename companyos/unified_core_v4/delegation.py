from .util import stable_id

CAPABILITY_AGENT={
"research":"research","product":"product","marketing":"marketing","finance":"finance",
"launch":"launch","operations":"operations","customer":"customer"
}

class Delegator:
    def __init__(self,db):
        self.db=db

    def delegate_goals(self):
        created=0
        for g in self.db.list_goals():
            if g["status"]!="ACTIVE": continue
            payload=g.get("payload",{})
            agent=payload.get("agent") or CAPABILITY_AGENT.get(payload.get("kind")) or "planner"
            tid=stable_id("goal-task",g["goal_id"],agent)
            self.db.add_task(tid,"goal_execution",g["title"],g["priority"],agent,
                             {"goal_id":g["goal_id"],"venture_id":g.get("venture_id"),"goal":g["title"],"payload":payload})
            created+=1
        return created
