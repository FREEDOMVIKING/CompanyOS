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

class FinancialForecasting:
    def __init__(self,home):
        self.home=home;self.runtime=home/"companyos_runtime"/"operator_35001_40000"
    def run(self):
        latest=read_json(self.home/"companyos_runtime"/"venture_builder"/"latest_build.json",{})
        revenue=latest.get("components",{}).get("revenue",{})
        baseline=revenue.get("baseline",{})
        monthly=float(baseline.get("monthly_revenue",0) or 0)
        profit=float(baseline.get("monthly_profit",0) or 0)
        result={"generated_at":now(),"venture":latest.get("title"),"forecast":{"monthly_revenue":monthly,"monthly_profit":profit,"annual_revenue":round(monthly*12,2),"annual_profit":round(profit*12,2)},"confidence":"low_until_real_data","status":"active"}
        write_json(self.runtime/"financial_forecast.json",result)
        return result
