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

class ExecutiveMemory:
    def __init__(self,home):
        self.home=home
        self.runtime=home/"companyos_runtime"/"operator_35001_40000"
    def run(self):
        sources=[
            self.home/"companyos_runtime"/"ceo_planner"/"latest_plan.json",
            self.home/"companyos_runtime"/"learning_engine"/"latest_learning.json",
            self.home/"companyos_runtime"/"opportunity_engine"/"ranking.json",
            self.home/"companyos_runtime"/"venture_builder"/"build_history.json",
        ]
        memory=[]
        for path in sources:
            data=read_json(path,{})
            if data:
                memory.append({"source":str(path),"data":data})
        result={"phase":"35001-40000","generated_at":now(),"memory_items":len(memory),"records":memory[-50:],"status":"active"}
        write_json(self.runtime/"executive_memory.json",result)
        return result
