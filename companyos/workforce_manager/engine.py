import json
import os
import tempfile
from datetime import datetime, timezone
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

def now():
    return datetime.now(timezone.utc).isoformat()

class WorkforceManager:
    def __init__(self,home):
        self.home=home;self.runtime=home/"companyos_runtime"/"operator_35001_40000"
    def run(self):
        agents=read_json(self.home/"companyos_runtime"/"opscenter"/"latest_ops_snapshot.json",{}).get("agent_registry",{})
        pools={}
        for aid,data in agents.items():
            pool=data.get("pool","general")
            pools.setdefault(pool,[]).append({"agent_id":aid,"reliability":data.get("reliability",0.5)})
        result={"generated_at":now(),"agent_count":len(agents),"pools":pools,"capacity_policy":"assign highest reliability available agent","status":"active"}
        write_json(self.runtime/"workforce_plan.json",result)
        return result
