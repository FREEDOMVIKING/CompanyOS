import json
from pathlib import Path
class StrategyExecutionState:
    """931: persistent adaptive closed-loop execution state."""
    def __init__(self,root):
        self.path=Path(root)/".companyos_runtime"/"adaptive_strategy_execution_state.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)
    def load(self):
        if not self.path.exists():return {}
        try:
            d=json.loads(self.path.read_text(encoding="utf-8"))
            return d if isinstance(d,dict) else {}
        except Exception:return {}
    def save(self,key,state):
        d=self.load(); d[str(key)]=state
        self.path.write_text(json.dumps(d,indent=2,default=str),encoding="utf-8")
        return state
