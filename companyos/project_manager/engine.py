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

class ProjectManager:
    def __init__(self,home):
        self.home=home;self.runtime=home/"companyos_runtime"/"operator_35001_40000"
    def run(self):
        latest=read_json(self.home/"companyos_runtime"/"venture_builder"/"latest_build.json",{})
        checklist=latest.get("components",{}).get("launch_checklist",[])
        tasks=[]
        previous=None
        for i,item in enumerate(checklist,1):
            task_id=f"task-{i}"
            tasks.append({"task_id":task_id,"name":item.get("item"),"status":item.get("status","pending"),"depends_on":[previous] if previous else []})
            previous=task_id
        result={"generated_at":now(),"venture":latest.get("title"),"task_count":len(tasks),"tasks":tasks,"status":"active" if latest else "waiting_for_venture"}
        write_json(self.runtime/"project_plan.json",result)
        return result
