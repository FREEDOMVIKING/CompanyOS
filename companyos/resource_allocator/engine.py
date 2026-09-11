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

class ResourceAllocator:
    def __init__(self,home):self.home=Path(home);self.out=self.home/"companyos_runtime"/"operator_35001_40000"/"resource_allocation.json"
    def run(self):
        ranking=read_json(self.home/"companyos_runtime"/"opportunity_engine"/"ranking.json",[])
        vals=[(x.get("title"),max(.01,float(x.get("score",0) or 0))) for x in ranking[:10]]
        total=sum(v for _,v in vals) or 1
        r={"generated_at":now(),"allocations":[{"venture":n,"capacity_share":round(v/total,4)} for n,v in vals],"status":"active"}
        write_json(self.out,r);return r
