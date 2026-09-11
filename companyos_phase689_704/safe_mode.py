import json
from pathlib import Path

class SafeMode:
    """699: persistent emergency stop for external execution."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "safe_mode.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def status(self):
        if not self.path.exists():
            return {"enabled":False}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return {"enabled":bool(data.get("enabled")),"reason":data.get("reason")}
        except Exception:
            return {"enabled":True,"reason":"invalid_safe_mode_state"}

    def enable(self, reason="manual"):
        data={"enabled":True,"reason":reason}
        self.path.write_text(json.dumps(data,indent=2),encoding="utf-8")
        return data

    def disable(self):
        data={"enabled":False,"reason":None}
        self.path.write_text(json.dumps(data,indent=2),encoding="utf-8")
        return data
