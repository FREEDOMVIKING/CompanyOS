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

class MultiCompanyOrchestrator:
    def __init__(self,home):
        self.home=home;self.runtime=home/"companyos_runtime"/"operator_35001_40000"
    def run(self):
        builds=read_json(self.home/"companyos_runtime"/"venture_builder"/"build_history.json",[])
        allocations=read_json(self.runtime/"resource_allocation.json",{}).get("allocations",[])
        companies=[]
        for build in builds:
            companies.append({"company_id":build.get("build_id"),"name":build.get("title"),"status":build.get("status"),"package_dir":build.get("package_dir")})
        result={"phase":"35001-40000","generated_at":now(),"company_count":len(companies),"companies":companies,"resource_allocations":allocations,"status":"active"}
        write_json(self.runtime/"multi_company_status.json",result)
        return result
