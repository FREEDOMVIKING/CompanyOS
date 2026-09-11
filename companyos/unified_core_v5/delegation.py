from .util import stable_id

class Delegator:
    def __init__(self,db,plugins):
        self.db=db; self.plugins=plugins

    def assign(self):
        caps=self.plugins.capabilities()
        created=0
        for g in self.db.list_goals():
            if g["status"]!="ACTIVE": continue
            p=g.get("payload",{})
            kind=p.get("kind")
            agent=p.get("agent") or "planner"
            plugin_id=(caps.get(kind) or [None])[0]
            tid=stable_id("goal-task",g["goal_id"],agent,plugin_id)
            self.db.add_task(tid,"goal_execution",g["title"],g["priority"],agent,
                             {"goal_id":g["goal_id"],"venture_id":g.get("venture_id"),"kind":kind},
                             plugin_id=plugin_id)
            created+=1
        return created
