import json
from pathlib import Path
class ExecutiveMemory:
    """91: durable executive lessons and decision summaries."""
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        if not self.path.exists():self.path.write_text("[]",encoding="utf-8")
    def add(self,item,limit=2000):
        try:data=json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:data=[]
        if not isinstance(data,list):data=[]
        data.append(dict(item));data=data[-max(1,int(limit)):]
        self.path.write_text(json.dumps(data,indent=2),encoding="utf-8");return data[-1]
    def recent(self,n=20):
        try:data=json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:data=[]
        return data[-max(1,int(n)):] if isinstance(data,list) else []
