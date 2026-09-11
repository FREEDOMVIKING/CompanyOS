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

class CEOCouncilV2:
    def __init__(self, home):
        self.home=home;self.runtime=home/"companyos_runtime"/"autonomy_40001_50000"
    def run(self):
        inputs={
            "strategy":read_json(self.home/"companyos_runtime"/"operator_35001_40000"/"strategic_plan.json",{}),
            "risk":read_json(self.home/"companyos_runtime"/"operator_35001_40000"/"risk_report.json",{}),
            "finance":read_json(self.home/"companyos_runtime"/"operator_35001_40000"/"financial_forecast.json",{}),
            "sales":read_json(self.home/"companyos_runtime"/"sales_engine"/"latest_sales_plan.json",{}),
        }
        votes=[
            {"role":"strategy","vote":"proceed" if inputs["strategy"].get("priorities") else "wait"},
            {"role":"risk","vote":"proceed" if inputs["risk"].get("status","clear")=="clear" else "review"},
            {"role":"finance","vote":"proceed" if inputs["finance"].get("forecast",{}).get("monthly_profit",0)>=0 else "revise"},
            {"role":"sales","vote":"proceed" if inputs["sales"].get("status")=="ready" else "wait"},
        ]
        proceed=sum(1 for x in votes if x["vote"]=="proceed")
        result={"phase":"40001-50000","generated_at":now(),"votes":votes,"decision":"advance" if proceed>=3 else "hold","proceed_votes":proceed,"status":"active"}
        write_json(self.runtime/"ceo_council_v2.json",result)
        return result
