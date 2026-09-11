import json
from pathlib import Path

class IntegrationRegistry:
    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"integration_registry.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists(): return {}
        try:
            d=json.loads(self.path.read_text(encoding="utf-8"))
            return d if isinstance(d,dict) else {}
        except Exception:
            return {}

    def register(self, name, kind, capabilities=None, enabled=True, metadata=None):
        d=self.load()
        d[name]={"name":name,"kind":kind,"capabilities":list(capabilities or []),
                 "enabled":bool(enabled),"metadata":metadata or {}}
        self.path.write_text(json.dumps(d,indent=2,default=str),encoding="utf-8")
        return d[name]

    def available(self, capability=None):
        rows=[x for x in self.load().values() if x.get("enabled")]
        if capability:
            rows=[x for x in rows if capability in x.get("capabilities",[])]
        return rows
