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
class LaunchEngine:
    def __init__(self,home):
        self.home=home;self.runtime=home/"companyos_runtime"/"launch_engine";self.runtime.mkdir(parents=True,exist_ok=True)
    def run(self):
        latest=read_json(self.home/"companyos_runtime"/"venture_builder"/"latest_build.json",{})
        checklist=latest.get("components",{}).get("launch_checklist",[])
        result={"generated_at":datetime.now(timezone.utc).isoformat(),"venture":latest.get("title"),"package_dir":latest.get("package_dir"),"checklist":checklist,"deployment_status":"waiting_for_configured_hosting_connector","status":"prepared" if latest else "waiting_for_venture"}
        write_json(self.runtime/"latest_launch_plan.json",result);return result
