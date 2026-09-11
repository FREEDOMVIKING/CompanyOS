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

class CompetitorIntelligence:
    def __init__(self, home):
        self.home=home;self.runtime=home/"companyos_runtime"/"autonomy_40001_50000"
    def run(self):
        ranking=read_json(self.home/"companyos_runtime"/"opportunity_engine"/"ranking.json",[])
        analyses=[]
        for item in ranking[:5]:
            comp=item.get("competitors",{})
            analyses.append({"venture":item.get("title"),"competitor_count":comp.get("count",0),"gaps":comp.get("gaps",[]),"research_status":item.get("research_plan",{}).get("status","waiting_for_provider")})
        result={"generated_at":now(),"analyses":analyses,"status":"active"}
        write_json(self.runtime/"competitor_intelligence.json",result)
        return result
