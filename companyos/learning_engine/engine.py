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
class LearningEngine:
    def __init__(self,home):
        self.home=home;self.runtime=home/"companyos_runtime"/"learning_engine";self.runtime.mkdir(parents=True,exist_ok=True)
    def run(self):
        opp=read_json(self.home/"companyos_runtime"/"opportunity_engine"/"ranking.json",[])
        builds=read_json(self.home/"companyos_runtime"/"venture_builder"/"build_history.json",[])
        lessons=[]
        if opp and not builds:lessons.append("top opportunities are not yet being converted into venture builds")
        if builds:lessons.append("venture build pipeline is operational")
        lessons.append("configured email connector is available for approved automation policy")
        result={"generated_at":datetime.now(timezone.utc).isoformat(),"lessons":lessons,"recommended_improvements":["connect live research provider","configure hosting provider","track real lead and revenue outcomes"],"status":"learned"}
        write_json(self.runtime/"latest_learning.json",result);return result
