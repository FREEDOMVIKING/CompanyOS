import json
from pathlib import Path

class AgentReturnBus:
    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"agent_return_bus.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def publish(self, result):
        rows=self.read_all()
        rows.append(result)
        self.path.write_text(json.dumps(rows,indent=2,default=str),encoding="utf-8")
        return result

    def read_all(self):
        if not self.path.exists(): return []
        try:
            d=json.loads(self.path.read_text(encoding="utf-8"))
            return d if isinstance(d,list) else []
        except Exception: return []
