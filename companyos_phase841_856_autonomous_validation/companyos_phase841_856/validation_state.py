import json
from pathlib import Path
class ValidationState:
    """853: persistent validation state."""
    def __init__(self,root):
        self.path=Path(root)/".companyos_runtime"/"validation_state.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)
    def load(self):
        if not self.path.exists(): return {}
        try:
            x=json.loads(self.path.read_text(encoding="utf-8"))
            return x if isinstance(x,dict) else {}
        except Exception: return {}
    def save(self,venture_id,state):
        d=self.load(); d[str(venture_id)]=state
        self.path.write_text(json.dumps(d,indent=2,default=str),encoding="utf-8")
        return state
