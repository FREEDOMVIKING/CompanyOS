import json
from pathlib import Path

class ConnectorRegistry:
    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"connector_registry.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def load(self):
        if not self.path.exists(): return {}
        try:
            d=json.loads(self.path.read_text(encoding="utf-8"))
            return d if isinstance(d,dict) else {}
        except Exception:
            return {}

    def register(self, name, connector_type, capabilities, priority=.5, enabled=True, metadata=None):
        d=self.load()
        d[name]={
            "name":name,
            "connector_type":connector_type,
            "capabilities":list(capabilities or []),
            "priority":float(priority),
            "enabled":bool(enabled),
            "metadata":metadata or {}
        }
        self.path.write_text(json.dumps(d,indent=2),encoding="utf-8")
        return d[name]

    def list_enabled(self):
        return [x for x in self.load().values() if x.get("enabled")]
