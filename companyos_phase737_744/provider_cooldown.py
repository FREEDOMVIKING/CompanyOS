import json
from pathlib import Path
from datetime import datetime,timezone,timedelta
class ProviderCooldown:
    def __init__(self,root):
        self.path=Path(root)/".companyos_runtime"/"provider_cooldowns.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)
    def load(self):
        if not self.path.exists(): return {}
        try:
            x=json.loads(self.path.read_text(encoding="utf-8"))
            return x if isinstance(x,dict) else {}
        except Exception: return {}
    def set(self,provider,seconds,reason):
        until=datetime.now(timezone.utc)+timedelta(seconds=max(1,int(seconds)))
        d=self.load(); d[provider]={"until":until.isoformat(),"reason":reason}
        self.path.write_text(json.dumps(d,indent=2),encoding="utf-8")
        return d[provider]
    def active(self,provider):
        item=self.load().get(provider)
        if not item: return False
        try: return datetime.fromisoformat(item["until"])>datetime.now(timezone.utc)
        except Exception: return True
