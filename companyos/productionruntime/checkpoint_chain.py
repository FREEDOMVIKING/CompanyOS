import json
from pathlib import Path
from datetime import datetime, timezone

class CheckpointChain:
    def __init__(self, root):
        self.dir=Path(root)/".companyos_runtime"/"checkpoints"
        self.dir.mkdir(parents=True,exist_ok=True)

    def save(self, state):
        ts=datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        path=self.dir/f"checkpoint_{ts}.json"
        row={"timestamp":datetime.now(timezone.utc).isoformat(),"state":state}
        path.write_text(json.dumps(row,indent=2,default=str),encoding="utf-8")
        return {"path":str(path),"timestamp":row["timestamp"]}

    def latest(self):
        files=sorted(self.dir.glob("checkpoint_*.json"))
        if not files:return {}
        try:return json.loads(files[-1].read_text(encoding="utf-8"))
        except Exception:return {}
