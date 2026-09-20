#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
source "$HOME/.companyos_launch_env" 2>/dev/null || true

STAMP="$(date +%Y%m%d_%H%M%S)"
BK="$HOME/companyos/.companyos_backups/compoundctl_v10_$STAMP"
mkdir -p "$BK"
cp -a scripts/companyos_compoundctl "$BK/" 2>/dev/null || true

cat > scripts/companyos_compoundctl <<'PY'
#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from companyos.runtime import compounding_capability_expansion as mod

def jread(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return {}

def dump(obj):
    print(json.dumps(obj,indent=2,sort_keys=True,default=str))

def resolve_path(name, fallback):
    p=getattr(mod,name,None)
    if p:
        return Path(p)
    return ROOT/fallback

STATE=resolve_path("STATE",".companyos_runtime/capability_expansion/compounding_state.json")
QUEUE=resolve_path("QUEUE",".companyos_runtime/capability_expansion/next_capability_queue.json")
EVENTS=resolve_path("EVENTS",".companyos_runtime/capability_expansion/compounding_events.jsonl")

def status():
    state=jread(STATE)
    queue=jread(QUEUE)
    reqs=queue.get("requests",[]) if isinstance(queue,dict) else []
    active=sum(1 for r in reqs if isinstance(r,dict) and r.get("status") not in ("completed","rejected","cancelled"))
    dump({
        "ok":True,
        "state_path":str(STATE),
        "queue_path":str(QUEUE),
        "events_path":str(EVENTS),
        "state":state,
        "request_summary":{
            "total":len(reqs),
            "active":active,
            "completed":sum(1 for r in reqs if isinstance(r,dict) and r.get("status")=="completed"),
            "rejected":sum(1 for r in reqs if isinstance(r,dict) and r.get("status")=="rejected"),
        },
        "latest_requests":reqs[-10:],
    })
    return 0

def once():
    fn=getattr(mod,"once",None)
    if not callable(fn):
        raise RuntimeError("compounding module does not expose once()")
    result=fn()
    dump({"ok":True,"result":result})
    return 0

def events():
    if not EVENTS.exists():
        dump({"events":[],"reason":"no_event_artifact_found","expected_path":str(EVENTS)})
        return 0
    lines=EVENTS.read_text(errors="replace").splitlines()[-50:]
    parsed=[]
    for line in lines:
        try:parsed.append(json.loads(line))
        except Exception:parsed.append({"raw":line})
    dump({"event_source":str(EVENTS),"events":parsed})
    return 0

def requests():
    q=jread(QUEUE)
    reqs=q.get("requests",[]) if isinstance(q,dict) else []
    dump({"request_count":len(reqs),"requests":reqs})
    return 0

def main():
    cmd=sys.argv[1] if len(sys.argv)>1 else "status"
    if cmd=="status":return status()
    if cmd=="once":return once()
    if cmd=="events":return events()
    if cmd=="requests":return requests()
    print("usage: scripts/companyos_compoundctl {status|once|events|requests}")
    return 2

if __name__=="__main__":
    raise SystemExit(main())
PY

chmod +x scripts/companyos_compoundctl

echo "[1/6] Compile"
python -m py_compile scripts/companyos_compoundctl companyos/runtime/compounding_capability_expansion.py

echo "[2/6] Interface contract"
python - <<'PY'
import sys
from pathlib import Path
root=Path.cwd()
sys.path.insert(0,str(root))
from companyos.runtime import compounding_capability_expansion as m
assert callable(getattr(m,"once",None)), "once() missing"
for name in ("STATE","QUEUE","EVENTS"):
    assert hasattr(m,name), f"{name} missing"
print("REAL_INTERFACE_CONTRACT=PASS")
print("STATE=",m.STATE)
print("QUEUE=",m.QUEUE)
print("EVENTS=",m.EVENTS)
PY

echo "[3/6] Status"
scripts/companyos_compoundctl status

echo "[4/6] One real compounding cycle"
scripts/companyos_compoundctl once

echo "[5/6] Requests/events"
scripts/companyos_compoundctl requests
scripts/companyos_compoundctl events

echo "[6/6] Git checkpoint"
git add scripts/companyos_compoundctl
git diff --cached --quiet || git commit -m "Fix compound control for real function-based runtime interface"
BRANCH="$(git branch --show-current)"
[ -n "$BRANCH" ] && git push origin "$BRANCH" || true

echo
echo "===== FINAL STATUS ====="
scripts/companyos_compoundctl status
echo
echo "BACKUP=$BK"
echo "COMPANYOS_COMPOUNDCTL_REAL_INTERFACE_V10=PASS"
