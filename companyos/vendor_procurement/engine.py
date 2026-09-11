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

class VendorProcurement:
    def __init__(self,home):
        self.home=home;self.runtime=home/"companyos_runtime"/"operator_35001_40000"
    def run(self):
        latest=read_json(self.home/"companyos_runtime"/"venture_builder"/"latest_build.json",{})
        vendor_plan=latest.get("components",{}).get("vendors",{})
        result={"generated_at":now(),"venture":latest.get("title"),"vendor_plan":vendor_plan,"sourcing_status":"research_required","commitments":"approval_required","status":"active"}
        write_json(self.runtime/"vendor_plan.json",result)
        return result
