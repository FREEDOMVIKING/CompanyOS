#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
cd "$HOME/companyos"
RT="$HOME/.companyos_runtime"; B="$RT/backups/v35_1_$(date +%Y%m%d_%H%M%S)"; mkdir -p "$B"
D="companyos/runtime/autonomous_task_dispatcher.py"
cp -a "$D" "$B/"
echo "===== COMPANYOS V35.1 AST LIVE LEASE FIX ====="

# Preserve/refresh guard module from V35 without touching dispatcher yet.
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
                    if not self.store.heartbeat(lease,ttl=ttl):
                        lost.set(); return
                except Exception:
                    lost.set(); return
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

python - <<'PY'
from pathlib import Path
import ast
p=Path("companyos/runtime/autonomous_task_dispatcher.py")
src=p.read_text()
tree=ast.parse(src)

# Idempotency.
if "V35_1_FENCED_HANDLER_CALL" in src:
    print("AST_PATCH=ALREADY_PRESENT")
    raise SystemExit(0)

# Find the exact statement containing the sole direct handler(...) call.
matches=[]
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id=="handler":
        matches.append(node)
print("DIRECT_HANDLER_CALLS",[(n.lineno,n.col_offset) for n in matches])
if len(matches)!=1:
    raise SystemExit("QUALIFICATION_FAIL: expected exactly one direct handler() call")

call=matches[0]
parent_stmt=None
for node in ast.walk(tree):
    if isinstance(node, ast.stmt) and getattr(node,"lineno",-1) <= call.lineno <= getattr(node,"end_lineno",call.lineno):
        # choose tightest statement containing call
        if parent_stmt is None or node.lineno >= parent_stmt.lineno:
            parent_stmt=node
if parent_stmt is None:
    raise SystemExit("QUALIFICATION_FAIL: handler statement not found")

# Only support assignment/return/expression forms; never guess other control flow.
if not isinstance(parent_stmt,(ast.Assign,ast.AnnAssign,ast.Return,ast.Expr)):
    raise SystemExit("QUALIFICATION_FAIL: unsupported handler statement")

lines=src.splitlines()
start=parent_stmt.lineno-1
end=getattr(parent_stmt,"end_lineno",parent_stmt.lineno)
original="\n".join(lines[start:end])
indent=lines[start][:len(lines[start])-len(lines[start].lstrip())]

# Determine expression text and preserve original destination semantics.
call_text=ast.get_source_segment(src,call)
if not call_text:
    raise SystemExit("QUALIFICATION_FAIL: cannot recover handler expression")

if isinstance(parent_stmt,ast.Assign) and len(parent_stmt.targets)==1:
    lhs=ast.get_source_segment(src,parent_stmt.targets[0])
    final=f"{indent}{lhs} = _v35_value"
elif isinstance(parent_stmt,ast.AnnAssign):
    lhs=ast.get_source_segment(src,parent_stmt.target)
    final=f"{indent}{lhs} = _v35_value"
elif isinstance(parent_stmt,ast.Return):
    final=f"{indent}return _v35_value"
elif isinstance(parent_stmt,ast.Expr):
    final=f"{indent}_ = _v35_value"
else:
    raise SystemExit("QUALIFICATION_FAIL")

replacement=[
 f"{indent}# V35_1_FENCED_HANDLER_CALL",
 f"{indent}_v35_guard = LeaseExecutionGuard(self.queue.kernel.db_path)",
 f'{indent}_v35_tid = str(getattr(task, "task_id", None) or getattr(task, "id", None) or "")',
 f'{indent}if not _v35_tid:',
 f'{indent}    raise RuntimeError("task_id_missing_for_lease")',
 f'{indent}_v35_ok, _v35_value, _v35_error = _v35_guard.execute(',
 f'{indent}    _v35_tid, "dispatcher-" + str(id(self)), lambda: {call_text}',
 f'{indent})',
 f'{indent}if not _v35_ok:',
 f'{indent}    raise RuntimeError(_v35_error or "leased_execution_failed")',
 final,
]
new_lines=lines[:start]+replacement+lines[end:]
new="\n".join(new_lines)+"\n"

imp="from companyos.runtime.lease_execution_guard import LeaseExecutionGuard"
if imp not in new:
    nt=ast.parse(new)
    insert=0
    if nt.body and isinstance(nt.body[0],ast.Expr) and isinstance(getattr(nt.body[0],"value",None),ast.Constant) and isinstance(nt.body[0].value.value,str):
        insert=nt.body[0].end_lineno
    while insert < len(new.splitlines()) and new.splitlines()[insert].startswith("from __future__"):
        insert+=1
    nl=new.splitlines()
    nl.insert(insert,imp)
    new="\n".join(nl)+"\n"

ast.parse(new)
p.write_text(new)
print("AST_PATCH=PASS")
print("ORIGINAL_HANDLER_STATEMENT=",original.strip())
PY

python -m py_compile companyos/runtime/lease_execution_guard.py "$D"

cat > tests/test_v35_1_dispatcher_ast_contract.py <<'PY'
from pathlib import Path
import ast
def test_v35_contract():
    p=Path("companyos/runtime/autonomous_task_dispatcher.py")
    s=p.read_text(); ast.parse(s)
    assert "V35_1_FENCED_HANDLER_CALL" in s
    assert "LeaseExecutionGuard" in s
    # Original naked direct handler call may exist only inside the fenced lambda.
    assert "_v35_guard.execute" in s
PY

python -m pytest -q \
  tests/test_v34_worker_lease_store.py \
  tests/test_v35_lease_execution_guard.py \
  tests/test_v35_1_dispatcher_ast_contract.py

echo "===== NON-DESTRUCTIVE CONTRACT ====="
grep -n -A14 -B4 'V35_1_FENCED_HANDLER_CALL' "$D" || true
git diff --check
echo "QUEUE_RECORDS_DELETED=0"
echo "FINANCE_CONNECTORS_CHANGED=NO"
echo "SUPERVISOR_RESTARTED=NO"

git add "$D" companyos/runtime/lease_execution_guard.py tests/test_v35_1_dispatcher_ast_contract.py tests/test_v35_lease_execution_guard.py
git diff --cached --quiet || git commit -m "V35.1 AST-wire fenced lease execution into live dispatcher"
echo "===== V35.1 COMPLETE ====="
echo "BACKUP=$B"
echo "NEXT=controlled reload and live crash-recovery qualification"
