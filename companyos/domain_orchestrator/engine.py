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
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".")
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def now():
    return datetime.now(timezone.utc).isoformat()

class DomainOrchestrator:
    def __init__(self, home):
        self.home=home;self.runtime=home/"companyos_runtime"/"autonomy_40001_50000"
    def run(self):
        latest=read_json(self.home/"companyos_runtime"/"venture_builder"/"latest_build.json",{})
        title=latest.get("title","companyos venture")
        base="".join(c.lower() for c in title if c.isalnum())[:40] or "companyosventure"
        candidates=[base+".com",base+".ai","get"+base+".com",base+"hq.com"]
        result={"generated_at":now(),"venture":title,"candidates":candidates,"availability_status":"provider_check_required","purchase_status":"approval_required","status":"planned"}
        write_json(self.runtime/"domain_orchestrator.json",result)
        return result
