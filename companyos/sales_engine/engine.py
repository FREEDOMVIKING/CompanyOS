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
class SalesEngine:
    def __init__(self,home):
        self.home=home;self.runtime=home/"companyos_runtime"/"sales_engine";self.runtime.mkdir(parents=True,exist_ok=True)
    def run(self):
        latest=read_json(self.home/"companyos_runtime"/"venture_builder"/"latest_build.json",{})
        spec=latest.get("components",{}).get("product_spec",{})
        result={"generated_at":datetime.now(timezone.utc).isoformat(),"venture":latest.get("title"),"ideal_customer":spec.get("customer"),"qualification_questions":["Do they experience the problem now?","Do they control the budget?","Will they test a pilot?","Is the timing under 90 days?"],"pipeline":["prospect","qualified","pilot","customer"],"outreach_mode":"automatic_email_allowed_only_for_configured_recipient_policy","status":"ready" if latest else "waiting_for_venture"}
        write_json(self.runtime/"latest_sales_plan.json",result);return result
