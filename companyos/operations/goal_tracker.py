import json
from pathlib import Path

class PersistentGoalTracker:
    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"persistent_goals.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def load(self):
        if not self.path.exists(): return {}
        try:
            d=json.loads(self.path.read_text(encoding="utf-8"))
            return d if isinstance(d,dict) else {}
        except Exception:return {}

    def upsert(self, goal_id, objective, target=1.0, progress=0.0, horizon="weekly"):
        d=self.load()
        d[goal_id]={"goal_id":goal_id,"objective":objective,"target":float(target),
                    "progress":float(progress),"horizon":horizon,
                    "status":"complete" if progress>=target else "active"}
        self.path.write_text(json.dumps(d,indent=2,default=str),encoding="utf-8")
        return d[goal_id]

    def update_progress(self, goal_id, progress):
        d=self.load()
        if goal_id not in d: return None
        d[goal_id]["progress"]=float(progress)
        d[goal_id]["status"]="complete" if float(progress)>=float(d[goal_id].get("target",1)) else "active"
        self.path.write_text(json.dumps(d,indent=2,default=str),encoding="utf-8")
        return d[goal_id]
