import json
from pathlib import Path

class PersistentGoalGraph:
    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"goal_graph.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def load(self):
        if not self.path.exists(): return {"goals":{},"edges":[]}
        try:
            d=json.loads(self.path.read_text(encoding="utf-8"))
            return d if isinstance(d,dict) else {"goals":{},"edges":[]}
        except Exception:
            return {"goals":{},"edges":[]}

    def upsert_goal(self, goal_id, objective, priority=.5, status="active"):
        d=self.load()
        d.setdefault("goals",{})[goal_id]={
            "goal_id":goal_id,"objective":objective,
            "priority":float(priority),"status":status
        }
        self.path.write_text(json.dumps(d,indent=2),encoding="utf-8")
        return d["goals"][goal_id]

    def add_dependency(self, parent, child):
        d=self.load()
        edge={"from":parent,"to":child}
        if edge not in d.setdefault("edges",[]):
            d["edges"].append(edge)
        self.path.write_text(json.dumps(d,indent=2),encoding="utf-8")
        return edge
