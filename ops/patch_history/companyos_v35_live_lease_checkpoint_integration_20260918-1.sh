#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
cd "$HOME/companyos"
RT="$HOME/.companyos_runtime"; B="$RT/backups/v35_$(date +%Y%m%d_%H%M%S)"; mkdir -p "$B"
echo "===== COMPANYOS V35 FENCED LIVE EXECUTION ====="
cp -a companyos/runtime/autonomous_task_dispatcher.py "$B/" || true
cat > companyos/runtime/lease_execution_guard.py <<'PY'
from __future__ import annotations
import json, os, threading, time
from pathlib import Path
from typing import Any, Callable
from companyos.runtime.worker_lease_store import WorkerLeaseStore

class LeaseExecutionGuard:
    def __init__(self, db_path: Path):
        self.store=WorkerLeaseStore(Path(db_path))
        self.cp=Path.home()/".companyos_runtime"/"execution_checkpoints"
        self.cp.mkdir(parents=True,exist_ok=True)
    def _write(self, tid, data):
        p=self.cp/f"{tid}.json"; t=p.with_suffix(".tmp")
        t.write_text(json.dumps(data,sort_keys=True)); os.replace(t,p)
    def execute(self, tid:str, owner:str, fn:Callable[[],Any], ttl:float=90, interval:float=20):
        lease=self.store.claim(tid,owner,ttl=ttl)
        if lease is None: return False,None,"lease_unavailable"
        stop=threading.Event(); lost=threading.Event()
        def hb():
            while not stop.wait(max(.25,interval)):
                try:
                    if not self.store.heartbeat(lease,ttl=ttl): lost.set(); return
                except Exception: lost.set(); return
        self._write(tid,{"state":"claimed","owner":owner,"token":lease.token,"time":time.time()})
        th=threading.Thread(target=hb,daemon=True); th.start()
        try:
            val=fn()
            if lost.is_set() or not self.store.heartbeat(lease,ttl=ttl):
                self._write(tid,{"state":"lease_lost","time":time.time()})
                return False,None,"lease_lost"
            self._write(tid,{"state":"completed","time":time.time()})
            return True,val,None
        except Exception as e:
            self._write(tid,{"state":"failed","error":f"{type(e).__name__}: {e}","time":time.time()})
            return False,None,f"{type(e).__name__}: {e}"
        finally:
            stop.set(); th.join(timeout=2); self.store.release(lease)
PY
cat > tests/test_v35_lease_execution_guard.py <<'PY'
import tempfile,time
from pathlib import Path
from companyos.runtime.durable_execution_kernel import DurableExecutionKernel
from companyos.runtime.lease_execution_guard import LeaseExecutionGuard
def test_success():
    with tempfile.TemporaryDirectory() as d:
        k=DurableExecutionKernel(Path(d)); g=LeaseExecutionGuard(k.db_path)
        ok,v,e=g.execute("v35a","w",lambda:7,ttl=2,interval=.1)
        assert ok and v==7 and e is None
def test_duplicate_blocked():
    with tempfile.TemporaryDirectory() as d:
        k=DurableExecutionKernel(Path(d)); g=LeaseExecutionGuard(k.db_path)
        x=g.store.claim("v35b","x",ttl=10); assert x
        ok,v,e=g.execute("v35b","w",lambda:7)
        assert not ok and e=="lease_unavailable"
        g.store.release(x)
def test_long_work_heartbeat():
    with tempfile.TemporaryDirectory() as d:
        k=DurableExecutionKernel(Path(d)); g=LeaseExecutionGuard(k.db_path)
        ok,v,e=g.execute("v35c","w",lambda:(time.sleep(1.3) or 9),ttl=1,interval=.2)
        assert ok and v==9
PY
python -m py_compile companyos/runtime/lease_execution_guard.py tests/test_v35_lease_execution_guard.py
python -m pytest -q tests/test_v34_worker_lease_store.py tests/test_v35_lease_execution_guard.py
python - <<'PY'
from pathlib import Path
import ast,shutil
p=Path("companyos/runtime/autonomous_task_dispatcher.py"); s=p.read_text()
tree=ast.parse(s)
calls=[n.lineno for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="handler"]
print("HANDLER_CALL_LINES",calls)
if len(calls)!=1: raise SystemExit("QUALIFICATION_FAIL")
imp="from companyos.runtime.lease_execution_guard import LeaseExecutionGuard"
if imp not in s:
    lines=s.splitlines(); i=0
    while i<len(lines) and (not lines[i].strip() or lines[i].startswith("from __future__")): i+=1
    lines.insert(i,imp); s="\n".join(lines)+"\n"
needle="result = handler(task)"
if s.count(needle)!=1: raise SystemExit("PATCH_ABORT")
old=p.read_text()
line=next(x for x in old.splitlines() if needle in x); indent=line[:len(line)-len(line.lstrip())]
rep=indent+'# V35_FENCED_LIVE_EXECUTION\n'+indent+'_g = LeaseExecutionGuard(self.queue.kernel.db_path)\n'+indent+'_tid = str(getattr(task,"task_id",None) or getattr(task,"id",None) or "")\n'+indent+'if not _tid: raise RuntimeError("task_id_missing_for_lease")\n'+indent+'_ok, _value, _error = _g.execute(_tid, "dispatcher-"+str(id(self)), lambda: handler(task))\n'+indent+'if not _ok: raise RuntimeError(_error or "leased_execution_failed")\n'+indent+'result = _value'
s=s.replace(line,rep,1); ast.parse(s); p.write_text(s)
print("AST_PATCH=PASS")
PY
python -m py_compile companyos/runtime/autonomous_task_dispatcher.py
python -m pytest -q tests/test_v34_worker_lease_store.py tests/test_v35_lease_execution_guard.py
echo "LIVE_EXECUTION_LEASES=WIRED"
echo "CHECKPOINTING=WIRED"
echo "HEARTBEAT=WIRED"
echo "QUEUE_RECORDS_DELETED=0"
echo "FINANCE_CONNECTORS_CHANGED=NO"
echo "SUPERVISOR_RESTARTED=NO"
git add companyos/runtime/lease_execution_guard.py companyos/runtime/autonomous_task_dispatcher.py tests/test_v35_lease_execution_guard.py
git diff --cached --quiet || git commit -m "V35 wire fenced leases and checkpoints into live dispatcher"
echo "===== V35 COMPLETE ====="
echo "BACKUP=$B"
echo "NEXT=controlled live reload plus crash recovery qualification"
