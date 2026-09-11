import json
from pathlib import Path
import uuid

class AgentRegistry:
    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"agent_registry.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def load(self):
        if not self.path.exists():
            return {}
        try:
            d=json.loads(self.path.read_text(encoding="utf-8"))
            return d if isinstance(d,dict) else {}
        except Exception:
            return {}

    def create(self, role, skills=None, temporary=False):
        d=self.load()
        aid="agent_"+uuid.uuid4().hex[:10]
        d[aid]={"agent_id":aid,"role":role,"skills":list(skills or []),"temporary":bool(temporary),"status":"active"}
        self.path.write_text(json.dumps(d,indent=2),encoding="utf-8")
        return d[aid]

    def active(self):
        return [x for x in self.load().values() if x.get("status")=="active"]
