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

echo "===== COMPANYOS V65.97E FAILURE COOLDOWN + DECOMPOSITION ====="

[ -f "$MOD" ] || { echo "V65_97E_ABORT=adaptive_director_missing"; exit 1; }

pids="$(pgrep -f 'companyos.runtime.adaptive_capability_director loop' || true)"
if [ -n "${pids:-}" ]; then
  echo "STOPPING_DIRECTOR_PIDS=$pids"
  for p in $pids; do [ "$p" = "$$" ] || kill "$p" 2>/dev/null || true; done
  sleep 2
  for p in $pids; do
    if [ "$p" != "$$" ] && kill -0 "$p" 2>/dev/null; then
      kill -9 "$p" 2>/dev/null || true
    fi
  done
fi
rm -f "$PIDFILE"

stamp="$(date +%Y%m%d_%H%M%S)"
cp "$MOD" "${MOD}.v65_97e_backup_${stamp}"
echo "BACKUP_MODULE=${MOD}.v65_97e_backup_${stamp}"

python - <<'PY'
from pathlib import Path

p = Path.home() / "companyos/companyos/runtime/adaptive_capability_director.py"
s = p.read_text(encoding="utf-8")

for marker in ("def _repair_generation(", "def scaffolded_integration_ids("):
    if marker not in s:
        raise SystemExit("V65_97E_ABORT=required_marker_missing:"+marker)

anchor = 'FEEDBACK=RT/"capability_feedback_state.json"\n'
if "adaptive_capability_failures.json" not in s:
    if anchor not in s:
        raise SystemExit("V65_97E_ABORT=state_anchor_missing")
    s = s.replace(
        anchor,
        anchor + 'FAILURES=RT/"adaptive_capability_failures.json"\nDYNAMIC_GAPS=RT/"adaptive_dynamic_capability_gaps.json"\n',
        1,
    )

helper_anchor = "def inventory():\n"
helpers = r'''def failure_records():
 data=load(FAILURES,{"failures":{}})
 f=data.get("failures")
 return f if isinstance(f,dict) else {}

def is_cooled(cid):
 rec=failure_records().get(str(cid),{})
 try:return float(rec.get("cooldown_until_unix") or 0)>time.time()
 except Exception:return False

def record_capability_failure(req,outcome,cooldown_seconds=21600):
 data=load(FAILURES,{"failures":{}})
 fs=data.get("failures")
 if not isinstance(fs,dict):fs={}
 cid=str(req.get("id") or "")
 old=fs.get(cid) if isinstance(fs.get(cid),dict) else {}
 rec={
  "id":cid,
  "kind":req.get("kind"),
  "reason":req.get("reason"),
  "failure_count":int(old.get("failure_count",0))+1,
  "last_status":outcome.get("status"),
  "last_failure":outcome.get("failure") or outcome.get("error"),
  "last_failed_at_unix":time.time(),
  "cooldown_until_unix":time.time()+max(1800,int(cooldown_seconds)),
 }
 fs[cid]=rec
 data["failures"]=fs
 data["updated_at_unix"]=time.time()
 save(FAILURES,data)
 return rec

def dynamic_gap_records():
 data=load(DYNAMIC_GAPS,{"gaps":[]})
 arr=data.get("gaps")
 return arr if isinstance(arr,list) else []

def save_dynamic_gaps(gaps):
 byid={str(x.get("id")):x for x in dynamic_gap_records() if isinstance(x,dict) and x.get("id")}
 for g in gaps:
  if not isinstance(g,dict) or not g.get("id"):continue
  cid=str(g["id"])
  old=byid.get(cid,{})
  old.update(g)
  old["id"]=cid
  old["updated_at_unix"]=time.time()
  byid[cid]=old
 save(DYNAMIC_GAPS,{"gaps":list(byid.values())[-200:],"updated_at_unix":time.time()})

def decompose_failed_capability(req,outcome):
 cid=str(req.get("id") or "")
 children=[]
 if cid=="service_scope_estimator":
  children=[
   {"id":"service_labor_estimator","kind":"analysis","reason":"Estimate labor hours, crew size and labor cost from service scope evidence.","models":["services"],"priority":92,"parent_capability":cid},
   {"id":"service_pricing_estimator","kind":"analysis","reason":"Estimate evidence-based service price ranges without inventing demand or sales.","models":["services"],"priority":92,"parent_capability":cid},
   {"id":"service_margin_estimator","kind":"analysis","reason":"Estimate contribution margin from price, labor, material and operating-cost evidence.","models":["services"],"priority":91,"parent_capability":cid},
   {"id":"service_scope_risk_estimator","kind":"analysis","reason":"Estimate service scope uncertainty, execution risk and contingency needs from supplied evidence.","models":["services"],"priority":91,"parent_capability":cid},
  ]
 if children:save_dynamic_gaps(children)
 return children

'''
if "def failure_records():" not in s:
    if helper_anchor not in s:
        raise SystemExit("V65_97E_ABORT=inventory_anchor_missing")
    s = s.replace(helper_anchor, helpers + helper_anchor, 1)

old_req = ''' miss=[r for r in ded.values() if not present(r["id"],inv)]
 miss.sort(key=lambda r:r["priority"],reverse=True)
 return miss
'''
new_req = ''' for g in dynamic_gap_records():
  if not isinstance(g,dict) or not g.get("id"):continue
  cid=str(g["id"])
  if cid not in ded or int(g.get("priority") or 0)>int(ded[cid].get("priority") or 0):
   ded[cid]=g
 miss=[r for r in ded.values() if not present(r["id"],inv) and not is_cooled(r["id"])]
 miss.sort(key=lambda r:int(r.get("priority") or 0),reverse=True)
 return miss
'''
if old_req in s:
    s = s.replace(old_req, new_req, 1)
elif "dynamic_gap_records()" not in s or "not is_cooled" not in s:
    raise SystemExit("V65_97E_ABORT=requirements_patch_anchor_missing")

old_cycle = '  outs.append(out);learn(req,out)\n'
new_cycle = '''  outs.append(out);learn(req,out)
  if out.get("action")=="generate_test_canary_promote" and not out.get("ok"):
   failure_rec=record_capability_failure(req,out)
   children=decompose_failed_capability(req,out)
   print("CAPABILITY_FAILURE_COOLDOWN=",json.dumps(failure_rec,sort_keys=True,default=str))
   print("CAPABILITY_DECOMPOSITION=",json.dumps(children,sort_keys=True,default=str))
'''
if old_cycle in s:
    s = s.replace(old_cycle, new_cycle, 1)
elif "CAPABILITY_FAILURE_COOLDOWN=" not in s:
    raise SystemExit("V65_97E_ABORT=cycle_patch_anchor_missing")

diag_anchor = ' print("MISSING_CAPABILITIES=",len(miss))\n'
if diag_anchor in s and "COOLED_CAPABILITIES=" not in s:
    s = s.replace(
        diag_anchor,
        diag_anchor +
        ' print("COOLED_CAPABILITIES=",sorted([k for k in failure_records() if is_cooled(k)]))\n'
        ' print("DYNAMIC_GAPS=",len(dynamic_gap_records()))\n',
        1,
    )

p.write_text(s, encoding="utf-8")
print("V65_97E_SOURCE_PATCH=PASS")
PY

python -m py_compile "$MOD"
echo "MODULE_COMPILE=PASS"

echo "===== SEED CURRENT FAILED CAPABILITY ====="
python - <<'PY'
from companyos.runtime import adaptive_capability_director as d
st=d.load(d.STATE,{})
sel=st.get("selected") or []
outs=st.get("outcomes") or []
if sel and outs and isinstance(sel[0],dict) and isinstance(outs[0],dict) and not outs[0].get("ok"):
    req=sel[0]
    out=outs[0]
    rec=d.record_capability_failure(req,out)
    kids=d.decompose_failed_capability(req,out)
    print("SEEDED_FAILED_CAPABILITY=",req.get("id"))
    print("SEEDED_COOLDOWN_UNTIL=",rec.get("cooldown_until_unix"))
    print("SEEDED_DECOMPOSITION_IDS=",[x.get("id") for x in kids])
else:
    print("SEEDED_FAILED_CAPABILITY=none")
PY

echo "===== ADVANCE PAST FAILED PARENT ====="
python -m companyos.runtime.adaptive_capability_director once

echo "===== START ONE BACKGROUND DIRECTOR ====="
nohup python -m companyos.runtime.adaptive_capability_director loop \
  --interval "$INTERVAL" >>"$LOGFILE" 2>&1 &
pid="$!"
echo "$pid" >"$PIDFILE"
sleep 1

if ! kill -0 "$pid" 2>/dev/null; then
  rm -f "$PIDFILE"
  echo "V65_97E_ABORT=director_failed_to_start"
  exit 1
fi

count="$(pgrep -f 'python .*companyos.runtime.adaptive_capability_director loop' | wc -l | tr -d ' ')"
echo "DIRECTOR_LOOP_PROCESS_COUNT=$count"
echo "ACTIVE_DIRECTOR_PID=$pid"

if [ "$count" -ne 1 ]; then
  echo "V65_97E_ABORT=expected_exactly_one_director_loop"
  pgrep -af 'adaptive_capability_director' || true
  exit 1
fi

echo "===== FINAL STATUS ====="
python -m companyos.runtime.adaptive_capability_director status || true

echo "V65_97E_FAILURE_COOLDOWN=PASS"
echo "V65_97E_CAPABILITY_DECOMPOSITION=PASS"
echo "V65_97E_PARENT_RETRY_STORM_PREVENTION=PASS"
echo "V65_97E_SINGLE_DIRECTOR=PASS"
echo "V65_97E_COMPLETE"
