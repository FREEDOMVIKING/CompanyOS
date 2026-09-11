import json,os,tempfile
from datetime import datetime,timezone
from pathlib import Path

def read_json(path,default):
    try:return json.loads(Path(path).read_text())
    except Exception:return default

def write_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=str(path.parent),prefix=path.name+".")
    try:
        with os.fdopen(fd,"w") as f:
            json.dump(data,f,indent=2,sort_keys=True);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def now():
    return datetime.now(timezone.utc).isoformat()

class CustomerAcquisitionV2:
    def __init__(self,home):self.home=Path(home);self.out=self.home/"companyos_runtime"/"autonomy_40001_50000"/"customer_acquisition_v2.json"
    def run(self):
        latest=read_json(self.home/"companyos_runtime"/"venture_builder"/"latest_build.json",{})
        spec=latest.get("components",{}).get("product_spec",{})
        r={"generated_at":now(),"venture":latest.get("title"),"ideal_customer":spec.get("customer","target customer"),"funnel":["prospect","qualified","pilot","customer"],"status":"ready"}
        write_json(self.out,r);return r
