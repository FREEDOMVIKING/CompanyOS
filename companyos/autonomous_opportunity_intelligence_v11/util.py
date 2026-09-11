import json, hashlib, re
from pathlib import Path
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).isoformat()

def sid(*parts, length=24):
    raw="|".join(str(x) for x in parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:length]

def read_json(path, default=None):
    if default is None:
        default={}
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default

def norm_text(s):
    return re.sub(r"\s+"," ",str(s or "")).strip()

def clamp(v, lo=0, hi=100):
    return max(lo,min(hi,float(v)))
