import json,os,tempfile
from datetime import datetime,timezone
from pathlib import Path

def read_json(path,default):
    try:return json.loads(Path(path).read_text())
    except Exception:return default

def write_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=str(path.parent),prefix=path.name+".")
    try:
        with os.fdopen(fd,"w") as f:
            json.dump(data,f,indent=2,sort_keys=True);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def now():
    return datetime.now(timezone.utc).isoformat()

class StrategicPlanner:
    def __init__(self,home):self.home=Path(home);self.out=self.home/"companyos_runtime"/"operator_35001_40000"/"strategic_plan.json"
    def run(self):
        ranking=read_json(self.home/"companyos_runtime"/"opportunity_engine"/"ranking.json",[])
        builds=read_json(self.home/"companyos_runtime"/"venture_builder"/"build_history.json",[])
        priorities=[{"priority":i+1,"venture":x.get("title"),"score":x.get("score"),"action":x.get("decision",{}).get("action","validate")} for i,x in enumerate(ranking[:5])]
        if builds:priorities.insert(0,{"priority":0,"venture":builds[-1].get("title"),"action":"prepare_launch"})
        r={"generated_at":now(),"horizon_days":90,"priorities":priorities,"status":"planned"}
        write_json(self.out,r);return r
