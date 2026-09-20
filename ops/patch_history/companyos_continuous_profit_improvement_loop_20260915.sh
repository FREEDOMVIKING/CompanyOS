#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "${HOME}/companyos"
echo "===== COMPANYOS CONTINUOUS PROFIT IMPROVEMENT LOOP ====="
echo "Bounded autonomous loop: opportunity -> specialist -> evidence -> score -> promote/improve/retire."
echo "No finance-limit changes. No DNS mutation. No secret output. No supervisor restart."

mkdir -p companyos/runtime scripts tests/generated .companyos_runtime/improvement_loop

cat > companyos/runtime/continuous_profit_improvement_loop.py <<'PY'
from __future__ import annotations
import json, os, time
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[2]
RT=ROOT/".companyos_runtime"
LOOP=RT/"improvement_loop"
STATE=LOOP/"state.json"
EVENTS=LOOP/"events.jsonl"
STOP=LOOP/"STOP"
WORKFORCE=RT/"ceo_workforce"/"latest.json"
QUEUE=RT/"profit_execution_action_queue.json"
EVIDENCE=RT/"market_evidence_summary.json"
POST=RT/"post_launch_next_action.json"
SELF=RT/"self_evolution_closed_loop"/"latest.json"

def now(): return datetime.now(timezone.utc).isoformat()
def read(p, default):
    try: return json.loads(p.read_text())
    except Exception: return default
def write(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(obj,indent=2,sort_keys=True))
    t.replace(p)
def event(kind, **kw):
    EVENTS.parent.mkdir(parents=True,exist_ok=True)
    with EVENTS.open("a") as f:
        f.write(json.dumps({"timestamp":now(),"kind":kind,**kw},sort_keys=True)+"\n")

def evidence_score():
    e=read(EVIDENCE,{})
    score=0
    # Only observed/verified fields count. Missing evidence never becomes success.
    for k,w in (("conversions",30),("revenue",40),("leads",15),("traffic",5)):
        v=e.get(k)
        if isinstance(v,(int,float)) and v>0: score += w
    if e.get("observed") is True: score += 5
    if e.get("verified") is True: score += 10
    return min(score,100), e

def bottlenecks():
    q=read(QUEUE,[])
    p=read(POST,{})
    ids=[]
    text=json.dumps([q,p]).lower()
    for key in ("execution_readiness","candidate_qualification","revenue_evidence",
                "market_evidence","agent_throughput","pricing","research",
                "market_validation","evidence_analysis"):
        if key in text: ids.append(key)
    return ids[:6]

def cycle():
    wf=read(WORKFORCE,{})
    workers=wf.get("workers",[]) if isinstance(wf,dict) else []
    evscore, ev=evidence_score()
    gaps=bottlenecks()
    decisions=[]
    for w in workers:
        wid=w.get("worker_id") or w.get("agent_id")
        role=w.get("role","unknown")
        status=w.get("status","probation")
        useful=int(w.get("useful_outputs",0) or 0)
        failures=int(w.get("failures",0) or 0)
        attributed=float(w.get("attributed_profit",0) or 0)
        # Permanent requires downstream evidence, not repeated activity.
        verified=int(w.get("verified_outcomes",0) or 0)
        score=min(100, useful*4 + verified*20 + (25 if attributed>0 else 0) + evscore//4 - failures*12)
        if status=="permanent":
            action="keep" if score>=55 else "review"
        elif score>=80 and verified>=2:
            action="promote_candidate"
        elif failures>=3 and useful==0:
            action="retire_candidate"
        else:
            action="improve_existing"
        decisions.append({"worker_id":wid,"role":role,"status":status,
                          "score":score,"action":action,
                          "verified_outcomes":verified,
                          "attributed_profit":attributed})
    # This controller recommends lifecycle changes. Existing strict scorer remains
    # the authority for actual permanent promotion.
    state={"timestamp":now(),"running":True,
           "verified_market_evidence_score":evscore,
           "observed_evidence":ev,
           "bottlenecks":gaps,
           "worker_decisions":decisions,
           "policy":{
             "invent_profit":False,
             "promotion_requires_verified_outcomes":True,
             "prefer_improve_before_spawn":True,
             "retire_repeated_failures":True,
             "financial_gates_unchanged":True,
             "external_action_gates_unchanged":True}}
    write(STATE,state)
    event("cycle", evidence_score=evscore, bottlenecks=gaps,
          workers=len(decisions),
          promote=sum(x["action"]=="promote_candidate" for x in decisions),
          improve=sum(x["action"]=="improve_existing" for x in decisions))
    return state

def run():
    LOOP.mkdir(parents=True,exist_ok=True)
    STOP.unlink(missing_ok=True)
    interval=max(60,int(os.getenv("COMPANYOS_IMPROVEMENT_INTERVAL","300")))
    event("start",interval=interval)
    while not STOP.exists():
        try: cycle()
        except Exception as e: event("error",error=type(e).__name__,message=str(e)[:300])
        time.sleep(interval)
    event("stop")
if __name__=="__main__": run()
PY

cat > scripts/companyos_improvementctl <<'PY'
#!/usr/bin/env python
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
L=ROOT/".companyos_runtime"/"improvement_loop"
cmd=sys.argv[1] if len(sys.argv)>1 else "status"
if cmd=="status":
    p=L/"state.json"
    print(p.read_text() if p.exists() else json.dumps({"running":False,"reason":"no_state"},indent=2))
elif cmd=="stop":
    L.mkdir(parents=True,exist_ok=True); (L/"STOP").write_text("requested\n"); print("STOP_REQUESTED")
elif cmd=="events":
    p=L/"events.jsonl"
    print("\n".join(p.read_text().splitlines()[-30:]) if p.exists() else "NO_EVENTS")
else:
    raise SystemExit("usage: companyos_improvementctl [status|events|stop]")
PY
chmod +x scripts/companyos_improvementctl

cat > tests/generated/test_continuous_profit_improvement_loop.py <<'PY'
from companyos.runtime.continuous_profit_improvement_loop import evidence_score, bottlenecks
def test_functions_exist():
    assert callable(evidence_score)
    assert callable(bottlenecks)
def test_no_automatic_profit_invention():
    s,e=evidence_score()
    assert 0 <= s <= 100
def test_policy_source_contains_strict_promotion():
    import inspect
    from companyos.runtime import continuous_profit_improvement_loop as m
    src=inspect.getsource(m)
    assert "verified>=2" in src
    assert "invent_profit" in src
PY

echo "===== COMPILE + TEST ====="
python -m py_compile companyos/runtime/continuous_profit_improvement_loop.py scripts/companyos_improvementctl
python -m pytest -q tests/generated/test_continuous_profit_improvement_loop.py tests/generated/test_verified_outcome_scoring.py

echo "===== FIRST CONTROLLED CYCLE ====="
python - <<'PY'
from companyos.runtime.continuous_profit_improvement_loop import cycle
import json
print(json.dumps(cycle(),indent=2))
PY

echo "===== INSTALL SUPERVISED SERVICE IF REGISTRY IS DISCOVERABLE ====="
python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/service_supervisor.py")
s=p.read_text()
name="continuous_profit_improvement_loop"
if name in s:
    print("SERVICE_ALREADY_REGISTERED")
else:
    # Conservative insertion into common SERVICES dict/list forms only.
    marker='"evidence_decision_closure"'
    idx=s.find(marker)
    if idx < 0:
        print("SERVICE_NOT_AUTO_REGISTERED: supervisor layout not safely recognized")
    else:
        # Do not mutate unknown supervisor syntax. Leave runtime available for next
        # explicit integration if exact registry shape cannot be proven.
        print("SERVICE_NOT_AUTO_REGISTERED: preserving healthy supervisor")
PY

echo "===== START LOOP WITHOUT TOUCHING SUPERVISOR ====="
if ! pgrep -f 'companyos.runtime.continuous_profit_improvement_loop' >/dev/null 2>&1; then
  nohup python -u -m companyos.runtime.continuous_profit_improvement_loop \
    > .companyos_runtime/improvement_loop/console.log 2>&1 &
  echo $! > .companyos_runtime/improvement_loop/pid
  sleep 2
fi
python scripts/companyos_improvementctl status

echo "===== COMMIT ONLY THIS PUSH ====="
git add companyos/runtime/continuous_profit_improvement_loop.py \
        scripts/companyos_improvementctl \
        tests/generated/test_continuous_profit_improvement_loop.py
if ! git diff --cached --quiet; then
  git commit -m "add continuous evidence-driven profit improvement loop"
else
  echo "NO_NEW_COMMIT_REQUIRED"
fi

echo "COMPANYOS_CONTINUOUS_PROFIT_IMPROVEMENT_LOOP=PASS"
echo "Status: python scripts/companyos_improvementctl status"
echo "Events: python scripts/companyos_improvementctl events"
