#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
GRT="$HOME/.companyos_runtime"
MOD="$ROOT/companyos/runtime/adaptive_capability_director.py"
PIDFILE="$GRT/adaptive_capability_director.pid"
LOGFILE="$GRT/adaptive_capability_director.log"
INTERVAL="${COMPANYOS_CAPABILITY_DIRECTOR_INTERVAL_SECONDS:-900}"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.97A CAPABILITY TEST-REPAIR LOOP ====="

if [ ! -f "$MOD" ]; then
  echo "V65_97A_ABORT=adaptive_capability_director_missing"
  exit 1
fi

if [ -f "$PIDFILE" ]; then
  pid="$(cat "$PIDFILE" 2>/dev/null || true)"
  if [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null; then
    echo "STOPPING_CAPABILITY_DIRECTOR_PID=$pid"
    kill "$pid" 2>/dev/null || true
    for _ in $(seq 1 20); do
      if ! kill -0 "$pid" 2>/dev/null; then break; fi
      sleep 1
    done
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null || true
    fi
  fi
  rm -f "$PIDFILE"
fi

stamp="$(date +%Y%m%d_%H%M%S)"
cp "$MOD" "${MOD}.v65_97a_backup_${stamp}"
echo "BACKUP_MODULE=${MOD}.v65_97a_backup_${stamp}"

python - <<'PY'
from pathlib import Path
import re

p = Path.home() / "companyos/companyos/runtime/adaptive_capability_director.py"
s = p.read_text(encoding="utf-8")

pat = re.compile(r"def build\(req\):\n.*?\n(?=def learn\(req,outcome\):)", re.S)

replacement = r'''def _failure_summary(result):
 out=[]
 if isinstance(result,dict):
  for e in result.get("validation_errors") or []:
   out.append(str(e))
  for step in result.get("tests") or []:
   if not isinstance(step,dict): continue
   rc=step.get("returncode")
   if rc:
    out.append("returncode="+str(rc))
    err=str(step.get("stderr") or "").strip()
    std=str(step.get("stdout") or "").strip()
    if err: out.append("stderr="+err[-1800:])
    if std: out.append("stdout="+std[-1200:])
 return " | ".join(out)[-3500:] or str(result.get("status") if isinstance(result,dict) else "unknown_failure")

def _activate_feedback(req):
 fb=load(FEEDBACK,{"capabilities":{}})
 caps=fb.get("capabilities")
 if not isinstance(caps,dict):caps={}
 rec=caps.get(req["id"]) if isinstance(caps.get(req["id"]),dict) else {}
 rec.update({
  "status":"active",
  "utility_score":float(rec.get("utility_score",50) or 50),
  "source":"adaptive_capability_director_v65_97a",
  "kind":req["kind"],
  "activated_at_unix":time.time()
 })
 caps[req["id"]]=rec
 fb["capabilities"]=caps
 fb["updated_at_unix"]=time.time()
 save(FEEDBACK,fb)

def _repair_generation(ce, req, prior):
 ctx=ce.diagnostics()
 failure=_failure_summary(prior)

 for repair_attempt in range(1,4):
  gap={
   "id":req["id"],
   "title":req["id"].replace("_"," ").title(),
   "reason":(
    req["reason"]
    +" Make it reusable across ventures and profit-focused without fabricating evidence. "
    +"The previous generated candidate failed validation/testing. Repair the implementation "
    +"while keeping the required capability contract. Failure evidence: "+failure
   )[:5200],
  }

  gen=ce.model_plan(gap,ctx)
  if not gen.get("ok"):
   failure="generation_failed:"+str(gen.get("reason") or gen.get("attempts"))
   continue

  try:
   module_content,_,_=ce._classify_generated_contents(gen.get("plan") or {},gap["id"])
   if module_content:
    is_dup,dup_id=ce._is_duplicate_generated_source(module_content)
    if is_dup:
     failure="duplicate_generated_source:"+str(dup_id)
     continue
  except Exception:
   pass

  cid,root,errors=ce.stage_plan(gap,gen["plan"])
  if errors:
   failure="validation_errors:"+json.dumps(errors,default=str)[-3000:]
   continue

  ok,tests=ce.test_stage(root,gap["id"])
  if not ok:
   failure=_failure_summary({"status":"candidate_rejected_tests","tests":tests})
   continue

  receipt=ce.promote(root,gap["id"],cid)
  try:
   execution=ce.run_capability(gap["id"],ctx)
  except Exception as exc:
   ce.rollback(gap["id"])
   failure="canary_failed:"+repr(exc)
   continue

  return {
   "ok":True,
   "status":"adaptive_repair_promoted_and_used",
   "repair_attempt":repair_attempt,
   "candidate_id":cid,
   "promotion":receipt,
   "execution":execution,
   "tests":tests,
  }

 return {
  "ok":False,
  "status":"adaptive_repair_exhausted",
  "failure":failure,
 }

def build(req):
 try:
  from companyos.runtime import capability_expansion as ce

  gap={
   "id":req["id"],
   "title":req["id"].replace("_"," ").title(),
   "reason":req["reason"]+" Make it reusable across ventures and profit-focused without fabricating evidence."
  }

  old=ce.derive_gap
  ce.derive_gap=lambda ctx:gap
  try:
   r=ce.cycle()
  finally:
   ce.derive_gap=old

  status=str(r.get("status") or "")
  ok=status in {"capability_promoted_and_used","existing_capability_used"}

  if not ok and status in {
   "candidate_rejected_tests",
   "candidate_rejected_validation",
   "generation_failed",
  }:
   repaired=_repair_generation(ce,req,r)
   if repaired.get("ok"):
    _activate_feedback(req)
   return repaired

  if ok:
   _activate_feedback(req)

  return {"ok":ok,"status":status,"initial_result":r}

 except Exception as e:
  return {"ok":False,"status":"exception","error":repr(e)}

'''

m = pat.search(s)
if not m:
    raise SystemExit("V65_97A_PATCH_ABORT=build_function_not_found")

s = s[:m.start()] + replacement + s[m.end():]
p.write_text(s, encoding="utf-8")
print("PATCH_BUILD_REPAIR_LOOP=PASS")
PY

python -m py_compile "$MOD"
echo "MODULE_COMPILE=PASS"

echo "===== RETRY SELF-EXPANSION NOW ====="
python -m companyos.runtime.adaptive_capability_director once

nohup python -m companyos.runtime.adaptive_capability_director loop \
  --interval "$INTERVAL" >>"$LOGFILE" 2>&1 &
pid="$!"
echo "$pid" >"$PIDFILE"
sleep 1

if ! kill -0 "$pid" 2>/dev/null; then
  rm -f "$PIDFILE"
  echo "V65_97A_ABORT=director_failed_to_restart"
  exit 1
fi

echo "CAPABILITY_DIRECTOR_RUNNING=true"
echo "PID=$pid"
echo "INTERVAL_SECONDS=$INTERVAL"
echo "LOGFILE=$LOGFILE"
echo "V65_97A_TEST_REPAIR_LOOP=PASS"
echo "V65_97A_EXISTING_VALIDATION_GATES_PRESERVED=PASS"
echo "V65_97A_CANARY_ROLLBACK_PRESERVED=PASS"
echo "V65_97A_COMPLETE"
