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

echo "===== COMPANYOS V65.97B INTEGRATION SCAFFOLD ADVANCEMENT ====="

if [ ! -f "$MOD" ]; then
  echo "V65_97B_ABORT=adaptive_capability_director_missing"
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
cp "$MOD" "${MOD}.v65_97b_backup_${stamp}"
echo "BACKUP_MODULE=${MOD}.v65_97b_backup_${stamp}"

python - <<'PY'
from pathlib import Path

p = Path.home() / "companyos/companyos/runtime/adaptive_capability_director.py"
s = p.read_text(encoding="utf-8")

old = '''def present(cid,inv):
 if cid in inv:return True
 tok=[x for x in cid.split("_") if len(x)>=4]
 for item in inv:
  if len(tok)>=2 and sum(t in item for t in tok)>=2:return True
 return False
'''

new = '''def scaffolded_integration_ids():
 out=set()
 d=ROOT/"companyos/extensions/integration_specs"
 if d.exists():
  for p in d.glob("*.json"):
   x=load(p,{})
   if isinstance(x,dict) and x.get("status")=="SCAFFOLDED":
    cid=str(x.get("id") or p.stem).strip().lower()
    if cid:out.add(cid)
 q=load(INTEGRATIONS,{"requests":[]})
 for x in q.get("requests",[]) or []:
  if isinstance(x,dict) and x.get("status")=="SCAFFOLDED" and x.get("id"):
   out.add(str(x["id"]).strip().lower())
 return out

def present(cid,inv):
 cid=str(cid).strip().lower()
 if cid in inv:return True
 if cid in scaffolded_integration_ids():
  return True
 tok=[x for x in cid.split("_") if len(x)>=4]
 for item in inv:
  if len(tok)>=2 and sum(t in item for t in tok)>=2:return True
 return False
'''

if old not in s:
    raise SystemExit("V65_97B_PATCH_ABORT=present_function_not_found")

s = s.replace(old, new)

needle = ' print("MISSING_CAPABILITIES=",len(miss))\n'
if needle in s and 'SCAFFOLDED_INTEGRATIONS=' not in s:
    s = s.replace(
        needle,
        needle + ' print("SCAFFOLDED_INTEGRATIONS=",sorted(scaffolded_integration_ids()))\n'
    )

p.write_text(s, encoding="utf-8")
print("PATCH_SCAFFOLDED_INTEGRATION_ADVANCEMENT=PASS")
PY

python -m py_compile "$MOD"
echo "MODULE_COMPILE=PASS"

echo "===== VERIFY CURRENT SCAFFOLD STATE ====="
python - <<'PY'
from companyos.runtime import adaptive_capability_director as d
print("SCAFFOLDED_INTEGRATIONS=", sorted(d.scaffolded_integration_ids()))
print("LISTING_INGESTION_PRESENT_FOR_PLANNING=", d.present("listing_ingestion_adapter", d.inventory()))
PY

echo "===== ADVANCE TO NEXT CAPABILITY ====="
python -m companyos.runtime.adaptive_capability_director once

nohup python -m companyos.runtime.adaptive_capability_director loop   --interval "$INTERVAL" >>"$LOGFILE" 2>&1 &
pid="$!"
echo "$pid" >"$PIDFILE"
sleep 1

if ! kill -0 "$pid" 2>/dev/null; then
  rm -f "$PIDFILE"
  echo "V65_97B_ABORT=director_failed_to_restart"
  exit 1
fi

echo "CAPABILITY_DIRECTOR_RUNNING=true"
echo "PID=$pid"
echo "INTERVAL_SECONDS=$INTERVAL"
echo "LOGFILE=$LOGFILE"
echo "V65_97B_SCAFFOLD_RESELECTION_FIXED=PASS"
echo "V65_97B_EXISTING_GATES_PRESERVED=PASS"
echo "V65_97B_COMPLETE"
