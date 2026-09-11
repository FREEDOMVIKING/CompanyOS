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
class FinanceManager:
    def __init__(self,home):
        self.home=home;self.runtime=home/"companyos_runtime"/"finance_manager";self.runtime.mkdir(parents=True,exist_ok=True)
    def run(self):
        latest=read_json(self.home/"companyos_runtime"/"venture_builder"/"latest_build.json",{})
        revenue=latest.get("components",{}).get("revenue",{})
        result={"generated_at":datetime.now(timezone.utc).isoformat(),"venture":latest.get("title"),"revenue_scenarios":revenue,"expense_policy":"record before payment","capital_policy":"preserve reserve and fund measurable milestones","financial_execution":"proposal_only_until_connector_and_policy_allow","status":"active"}
        write_json(self.runtime/"latest_finance_plan.json",result);return result
