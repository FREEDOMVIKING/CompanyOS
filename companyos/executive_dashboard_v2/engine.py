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
class DashboardV2:
    def __init__(self,home):
        self.home=home;self.runtime=home/"companyos_runtime"/"executive_dashboard_v2";self.runtime.mkdir(parents=True,exist_ok=True)
    def snapshot(self):
        paths={
            "ceo_plan":self.home/"companyos_runtime"/"ceo_planner"/"latest_plan.json",
            "launch":self.home/"companyos_runtime"/"launch_engine"/"latest_launch_plan.json",
            "sales":self.home/"companyos_runtime"/"sales_engine"/"latest_sales_plan.json",
            "finance":self.home/"companyos_runtime"/"finance_manager"/"latest_finance_plan.json",
            "learning":self.home/"companyos_runtime"/"learning_engine"/"latest_learning.json",
            "portfolio":self.home/"companyos_runtime"/"growth_suite"/"portfolio.json",
        }
        result={"phase":"30001-35000","generated_at":datetime.now(timezone.utc).isoformat(),**{k:read_json(v,{}) for k,v in paths.items()}}
        write_json(self.runtime/"latest_snapshot.json",result);return result
