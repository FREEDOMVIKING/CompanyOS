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

class NegotiationEngine:
    def __init__(self, home):
        self.home=home;self.runtime=home/"companyos_runtime"/"autonomy_40001_50000"
    def run(self):
        latest=read_json(self.home/"companyos_runtime"/"venture_builder"/"latest_build.json",{})
        pricing=latest.get("components",{}).get("billing",{}).get("plans",[])
        floor=min([float(x.get("price",0) or 0) for x in pricing], default=0)
        target=max([float(x.get("price",0) or 0) for x in pricing], default=0)
        result={"generated_at":now(),"venture":latest.get("title"),"strategy":{"opening_position":target,"target":target,"floor":floor,"concessions":["pilot scope","payment timing","term length"]},"commitment_status":"draft_only_no_signature_no_payment","status":"ready"}
        write_json(self.runtime/"negotiation_engine.json",result)
        return result
