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

class SelfEvolution:
    def __init__(self, home):
        self.home=home
        self.runtime=home/"companyos_runtime"/"autonomy_40001_50000"
        self.output=home/"self_evolution_proposals"
        self.output.mkdir(parents=True,exist_ok=True)
    def run(self):
        risk=read_json(self.home/"companyos_runtime"/"operator_35001_40000"/"risk_report.json",{})
        lessons=read_json(self.home/"companyos_runtime"/"learning_engine"/"latest_learning.json",{})
        proposal={"generated_at":now(),"changes":[
            "add missing connector health coverage",
            "reduce unnecessary service restarts",
            "promote validated venture data into scoring",
        ],"inputs":{"risk_status":risk.get("status"),"lessons":lessons.get("recommended_improvements",[])},"apply_mode":"reviewed_patch_only","status":"proposal_generated"}
        filename=self.output/("proposal-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+".json")
        write_json(filename,proposal)
        write_json(self.runtime/"self_evolution.json",{**proposal,"proposal_file":str(filename)})
        return {**proposal,"proposal_file":str(filename)}
