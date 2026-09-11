import json, os, tempfile
from pathlib import Path

def read_json(path, default):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return default

def write_json(path, data):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=str(path.parent),prefix=path.name+".")
    try:
        with os.fdopen(fd,"w") as f:
            json.dump(data,f,indent=2,sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

from datetime import datetime, timezone

class CEOPlanner:
    def __init__(self,home):
        self.home=home
        self.runtime=home/"companyos_runtime"/"ceo_planner"
        self.runtime.mkdir(parents=True,exist_ok=True)

    def run(self):
        opportunities=read_json(self.home/"companyos_runtime"/"opportunity_engine"/"ranking.json",[])
        builds=read_json(self.home/"companyos_runtime"/"venture_builder"/"build_history.json",[])
        objectives=[]
        if opportunities:
            objectives.append({"priority":1,"objective":"validate_top_opportunity","venture":opportunities[0].get("title")})
        if opportunities and not builds:
            objectives.append({"priority":2,"objective":"build_top_venture","venture":opportunities[0].get("title")})
        if builds:
            objectives.append({"priority":2,"objective":"prepare_latest_venture_launch","venture":builds[-1].get("title")})
        objectives.append({"priority":3,"objective":"review_connector_health"})
        result={
            "phase":"30001-35000",
            "generated_at":datetime.now(timezone.utc).isoformat(),
            "objectives":sorted(objectives,key=lambda x:x["priority"]),
            "resource_policy":"allocate_to_highest_validated_expected_return",
            "status":"planned",
        }
        write_json(self.runtime/"latest_plan.json",result)
        return result
