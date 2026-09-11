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

class RiskCompliance:
    def __init__(self,home):self.home=Path(home);self.out=self.home/"companyos_runtime"/"operator_35001_40000"/"risk_report.json"
    def run(self):
        paths=[self.home/"companyos_runtime"/"connectors"/"health.json",self.home/"companyos_runtime"/"connectors_live"/"health.json"]
        data={}
        for p in paths:
            x=read_json(p,{})
            if x:data=x;break
        risks=[]
        for name,info in data.get("connectors",{}).items():
            if info.get("enabled") and not info.get("configured"):risks.append({"connector":name,"severity":"medium"})
        r={"generated_at":now(),"risk_count":len(risks),"risks":risks,"controls":["audit logging","approval gates","secret redaction"],"status":"clear" if not risks else "attention_required"}
        write_json(self.out,r);return r
