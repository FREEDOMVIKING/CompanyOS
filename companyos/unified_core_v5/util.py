import json, os, tempfile, hashlib
from pathlib import Path
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).isoformat()

def stable_id(*parts, length=24):
    raw="|".join(str(x) for x in parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:length]

def read_json(path, default=None):
    if default is None:
        default={}
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default

def atomic_write_json(path, data):
    path=Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+".", dir=str(path.parent))
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(data,f,indent=2,sort_keys=True,default=str)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):
            try: os.unlink(tmp)
            except OSError: pass
