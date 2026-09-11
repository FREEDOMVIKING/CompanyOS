import json, hashlib
from pathlib import Path
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).isoformat()

def sid(*parts, length=24):
    return hashlib.sha256("|".join(map(str,parts)).encode()).hexdigest()[:length]

def read_json(path, default=None):
    if default is None: default={}
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default

def write_json(path, data):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,indent=2,sort_keys=True,default=str),encoding="utf-8")
