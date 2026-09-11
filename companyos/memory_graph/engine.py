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

class MemoryGraph:
    def __init__(self,home):self.home=Path(home);self.out=self.home/"companyos_runtime"/"autonomy_40001_50000"/"memory_graph.json"
    def run(self):
        opp=read_json(self.home/"companyos_runtime"/"opportunity_engine"/"ranking.json",[])
        builds=read_json(self.home/"companyos_runtime"/"venture_builder"/"build_history.json",[])
        nodes=[{"id":"opp:"+str(x.get("opportunity_id")),"type":"opportunity","label":x.get("title")} for x in opp[:20]]
        nodes += [{"id":"venture:"+str(x.get("build_id")),"type":"venture","label":x.get("title")} for x in builds[:20]]
        r={"generated_at":now(),"node_count":len(nodes),"nodes":nodes,"status":"active"}
        write_json(self.out,r);return r
