#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACK="$HOME/.companyos_runtime/backups/v31_$STAMP"
mkdir -p "$BACK/companyos/runtime"
cp -a companyos/runtime/adaptive_workforce_execution_bridge.py "$BACK/companyos/runtime/"
cp -a companyos/runtime/default_specialist_registry.py "$BACK/companyos/runtime/"

echo "===== V31 DEEP INTEGRITY REPAIR ====="
python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/adaptive_workforce_execution_bridge.py")
s=p.read_text()
s=s.replace('ROOT = Path.home() / "companyos"\nRUNTIME = ROOT / ".companyos_runtime"\n',
            'ROOT = (Path.home() / "companyos").resolve()\n# V31_CANONICAL_RUNTIME_ROOT\nRUNTIME = Path.home() / ".companyos_runtime"\n')
s=s.replace('"source": str(QUEUE.relative_to(ROOT)),','"source": str(QUEUE),')
s=s.replace('"verified_results_feed": str(RESULTS.relative_to(ROOT)),','"verified_results_feed": str(RESULTS),')
old='if __name__ == "__main__":\n    print(json.dumps(cycle(), indent=2, default=str))\n'
new='if __name__ == "__main__":\n    # V31_LONG_RUNNING_SERVICE_ENTRYPOINT\n    run()\n'
assert old in s
s=s.replace(old,new)
p.write_text(s)
print("WORKFORCE_BRIDGE_PATCH=PASS")
PY

cat > companyos/runtime/default_specialist_registry.py <<'PY'
from __future__ import annotations
import hashlib, json, time
from pathlib import Path
from typing import Any
from companyos.runtime.autonomous_task_dispatcher import AutonomousTaskDispatcher

RUNTIME=Path.home()/".companyos_runtime"
EVIDENCE=RUNTIME/"specialist_evidence"
EVIDENCE.mkdir(parents=True,exist_ok=True)

def _payload(task)->dict[str,Any]:
    return task.payload if isinstance(task.payload,dict) else {}

def _text(p,*keys):
    for k in keys:
        v=p.get(k)
        if isinstance(v,str) and v.strip(): return v.strip()
    return ""

def _write(task,kind,body):
    safe="".join(c for c in str(task.task_id) if c.isalnum() or c in "-_")[:120]
    path=EVIDENCE/f"{safe}.{kind}.json"
    rec={"schema":"companyos.specialist_evidence.v1","task_id":task.task_id,
         "task_type":task.task_type,"created_at_unix":time.time(),**body}
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(rec,indent=2,sort_keys=True,default=str)+"\n")
    tmp.replace(path)
    return str(path)

def _require(ok,reason):
    if not ok: raise RuntimeError(reason)

def register_default_specialists(dispatcher:AutonomousTaskDispatcher)->None:
    # V31: evidence-backed internal specialists. No fabricated external work.
    def research(task):
        p=_payload(task)
        subject=_text(p,"topic","goal","directive","objective","query","name")
        _require(bool(subject),"research_missing_subject")
        supplied=p.get("evidence") or p.get("sources") or p.get("observations") or []
        if not isinstance(supplied,(list,dict)): supplied=[str(supplied)]
        artifact=_write(task,"research",{
            "subject":subject,
            "payload_sha256":hashlib.sha256(json.dumps(p,sort_keys=True,default=str).encode()).hexdigest(),
            "supplied_evidence":supplied,
            "external_research_performed":False,
            "status":"internal_research_intake_validated",
            "next_requirement":"use evidence acquisition connector when fresh external evidence is required"})
        return {"agent":"research_agent","status":"evidence_artifact_created",
                "artifact":artifact,"external_claims_invented":False}

    def planning(task):
        p=_payload(task)
        goal=_text(p,"goal","directive","objective","topic","name")
        _require(bool(goal),"planning_missing_goal")
        constraints=p.get("constraints",[])
        if not isinstance(constraints,list): constraints=[str(constraints)]
        steps=[
          {"stage":"validate_inputs","done_when":"required evidence is present"},
          {"stage":"select_execution_path","done_when":"dependencies and gates are resolved"},
          {"stage":"execute","done_when":"observable artifact or action result exists"},
          {"stage":"verify_outcome","done_when":"result evidence passes validation"}]
        artifact=_write(task,"plan",{"goal":goal,"constraints":constraints,
                                     "steps":steps,"status":"internal_plan_materialized"})
        return {"agent":"planning_agent","status":"plan_artifact_created",
                "artifact":artifact,"step_count":len(steps)}

    def build(task):
        p=_payload(task)
        name=_text(p,"name","goal","directive","objective","topic")
        _require(bool(name),"build_missing_target")
        artifact=_write(task,"build",{
            "target":name,"requested_artifact":p.get("artifact") or p.get("deliverable"),
            "inputs":p,"status":"build_manifest_materialized",
            "external_deployment_performed":False})
        _require(Path(artifact).exists() and Path(artifact).stat().st_size>0,
                 "build_artifact_not_persisted")
        return {"agent":"builder_agent","status":"build_artifact_created",
                "artifact":artifact,"external_deployment_performed":False}

    dispatcher.register(task_type="research",agent_name="research_agent",handler=research)
    dispatcher.register(task_type="planning",agent_name="planning_agent",handler=planning)
    dispatcher.register(task_type="build",agent_name="builder_agent",handler=build)
PY

python -m py_compile companyos/runtime/adaptive_workforce_execution_bridge.py companyos/runtime/default_specialist_registry.py
python - <<'PY'
from pathlib import Path
b=Path("companyos/runtime/adaptive_workforce_execution_bridge.py").read_text()
r=Path("companyos/runtime/default_specialist_registry.py").read_text()
assert 'RUNTIME = Path.home() / ".companyos_runtime"' in b
assert "V31_LONG_RUNNING_SERVICE_ENTRYPOINT" in b
assert "research_stub_completed" not in r and "build_stub:" not in r
assert "specialist_evidence.v1" in r
print("STATIC_INTEGRITY=PASS")
PY

echo "===== ISOLATED SPECIALIST TEST ====="
python - <<'PY'
import tempfile
from pathlib import Path
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_task_dispatcher import AutonomousTaskDispatcher
from companyos.runtime.default_specialist_registry import register_default_specialists
q=AutonomousTaskQueue(Path(tempfile.mkdtemp()))
d=AutonomousTaskDispatcher(q); register_default_specialists(d)
for typ,payload in [
 ("research",{"goal_id":"r","stage":"research","topic":"test opportunity"}),
 ("planning",{"goal_id":"p","stage":"planning","goal":"test opportunity"}),
 ("build",{"goal_id":"b","stage":"build","name":"test artifact"})]:
 t=q.enqueue(task_type=typ,payload=payload,priority=100,idempotency_key="v31-"+typ)
 res=d.dispatch_task(t)
 assert res.dispatched and res.reason=="completed",(typ,res)
 assert q.load(t.task_id).state=="COMPLETED"
 ap=res.result.get("artifact"); assert ap and Path(ap).exists()
 print("SPECIALIST",typ,"PASS")
bad=q.enqueue(task_type="research",payload={"goal_id":"bad","stage":"research"},
              priority=100,idempotency_key="v31-bad")
res=d.dispatch_task(bad)
assert res.reason=="handler_failed" and q.load(bad.task_id).state!="COMPLETED"
print("FALSE_COMPLETION_GUARD=PASS")
PY

echo "===== BRIDGE CONTRACT ====="
python - <<'PY'
from companyos.runtime.adaptive_workforce_execution_bridge import cycle
s=cycle()
assert s.get("running") is True and s.get("financial_metrics_invented") is False
print("BRIDGE_CYCLE=PASS")
PY

echo "===== CONTROLLED SERVICE RELOAD ====="
for pat in 'companyos.runtime.adaptive_workforce_execution_bridge' 'companyos.runtime.continuous_goal_runtime'; do
 for pid in $(pgrep -f "$pat" || true); do [ "$pid" = "$$" ] || kill "$pid" 2>/dev/null || true; done
done
SUP="$(pgrep -f 'companyos.runtime.service_supervisor' | head -1 || true)"
[ -n "$SUP" ] || { echo "FAIL=no_supervisor"; exit 10; }
C=""; W=""
for i in $(seq 1 45); do
 sleep 1
 C="$(pgrep -f 'companyos.runtime.continuous_goal_runtime' | tail -1 || true)"
 W="$(pgrep -f 'companyos.runtime.adaptive_workforce_execution_bridge' | tail -1 || true)"
 [ -n "$C" ] && [ -n "$W" ] && break
 echo "waiting_reload=${i}s"
done
[ -n "$C" ] && [ -n "$W" ] || { echo "FAIL=reload"; exit 11; }
echo "SUPERVISOR_PID=$SUP CONTINUOUS_PID=$C BRIDGE_PID=$W"

echo "===== 180 SECOND QUALIFICATION ====="
python - <<'PY'
import json,time,subprocess
from pathlib import Path
from collections import Counter
root=Path.home()/".companyos_runtime"/"task_queue"
ss=Path.home()/".companyos_runtime"/"service_supervisor_state.json"
def snap():
 c=Counter()
 for p in root.glob("*.json"):
  try:c[str(json.loads(p.read_text()).get("state","UNKNOWN")).upper()]+=1
  except Exception:c["UNREADABLE"]+=1
 return c
def services():
 try:return json.loads(ss.read_text()).get("services",{})
 except Exception:return {}
def alive(x):
 return subprocess.run(["pgrep","-f",x],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
a=snap(); b=a; print("T+000",dict(a),flush=True)
for sec in range(15,181,15):
 time.sleep(15); b=snap(); w=services().get("adaptive_workforce_execution_bridge",{})
 print(f"T+{sec:03d}",dict(b),
  "completed_delta=",b["COMPLETED"]-a["COMPLETED"],
  "queued_delta=",b["QUEUED"]-a["QUEUED"],
  "failed_delta=",b["FAILED"]-a["FAILED"],
  "bridge_running=",w.get("running"),"bridge_restarts=",w.get("restarts"),
  "bridge_failures=",w.get("consecutive_failures"),
  "sup=",alive("companyos.runtime.service_supervisor"),
  "child=",alive("companyos.runtime.continuous_goal_runtime"),flush=True)
print("FINAL_COMPLETED_DELTA=",b["COMPLETED"]-a["COMPLETED"])
print("FINAL_QUEUED_DELTA=",b["QUEUED"]-a["QUEUED"])
print("FINAL_FAILED_DELTA=",b["FAILED"]-a["FAILED"])
assert alive("companyos.runtime.service_supervisor")
assert alive("companyos.runtime.continuous_goal_runtime")
assert alive("companyos.runtime.adaptive_workforce_execution_bridge")
PY

echo "===== EVIDENCE AUDIT ====="
python - <<'PY'
import json
from pathlib import Path
root=Path.home()/".companyos_runtime"/"specialist_evidence"
rows=list(root.glob("*.json")); print("SPECIALIST_EVIDENCE_FILES=",len(rows))
valid=0
for p in rows[-100:]:
 try:
  d=json.loads(p.read_text())
  if d.get("schema")=="companyos.specialist_evidence.v1" and d.get("task_id"): valid+=1
 except Exception: pass
print("LAST_100_VALID_EVIDENCE=",valid)
assert rows
PY

echo "V31_COMPLETE"
echo "FALSE_STUB_COMPLETIONS_REMOVED=YES"
echo "WORKFORCE_BRIDGE_LONG_RUNNING=YES"
echo "CANONICAL_RUNTIME_ROOT=YES"
echo "QUEUE_RECORDS_DELETED=0"
echo "FINANCE_CONNECTORS_CHANGED=NO"
echo "SUPERVISOR_RESTARTED=NO"
echo "BACKUP=$BACK"
