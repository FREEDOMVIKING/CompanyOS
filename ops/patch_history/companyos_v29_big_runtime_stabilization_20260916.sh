#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACK="$HOME/.companyos_runtime/backups/v29_bigpush_$STAMP"
mkdir -p "$BACK/companyos/runtime"
FILES=(companyos/runtime/continuous_goal_runtime.py companyos/runtime/autonomous_ceo_runtime_service.py)
for f in "${FILES[@]}"; do cp -a "$f" "$BACK/$f"; done
restore(){ echo "V29_ROLLBACK"; for f in "${FILES[@]}"; do cp -a "$BACK/$f" "$f"; done; }
trap restore ERR

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/autonomous_ceo_runtime_service.py")
s=p.read_text()
if "V29_PERSISTENT_CEO_STATE" not in s:
    marker="    def startup(self) -> CEORuntimeServiceState:\n"
    assert marker in s
    lines=[
        "    # V29_PERSISTENT_CEO_STATE",
        "    def load(self) -> CEORuntimeServiceState:",
        "        if not self.state_path.exists():",
        "            return self.startup()",
        "        try:",
        "            raw = json.loads(self.state_path.read_text(encoding='utf-8'))",
        "            return CEORuntimeServiceState(**raw)",
        "        except Exception:",
        "            return self.startup()",
        "",
    ]
    s=s.replace(marker,"\n".join(lines)+"\n"+marker)
    p.write_text(s)
print("CEO_STATE_PATCH=PASS")
PY

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/continuous_goal_runtime.py")
s=p.read_text()
assert "V28_2_CONTINUOUS_EXECUTION_PUMP" in s
if "V29_BIG_RUNTIME_STABILIZATION" not in s:
    s=s.replace("    updated_at_unix: float = 0.0\n",
        "    updated_at_unix: float = 0.0\n"
        "    execution_dispatched: int = 0\n"
        "    execution_failures: int = 0\n"
        "    scheduler_failures: int = 0\n"
        "    ceo_failures: int = 0\n")
    old=("    def load(self):\n"
         "        if not self.state_path.exists():\n"
         "            return ContinuousGoalRuntimeState()\n"
         "        return ContinuousGoalRuntimeState(**json.loads(self.state_path.read_text()))\n")
    new=("    def load(self):\n"
         "        if not self.state_path.exists():\n"
         "            return ContinuousGoalRuntimeState()\n"
         "        try:\n"
         "            raw = json.loads(self.state_path.read_text())\n"
         "            allowed = ContinuousGoalRuntimeState.__dataclass_fields__\n"
         "            return ContinuousGoalRuntimeState(**{k:v for k,v in raw.items() if k in allowed})\n"
         "        except Exception:\n"
         "            return ContinuousGoalRuntimeState()\n")
    assert old in s
    s=s.replace(old,new)
    a=s.index("    def cycle(self, state):")
    b=s.index("    def run(self, max_cycles=0):",a)
    lines=[
"    def cycle(self, state):",
"        # V29_BIG_RUNTIME_STABILIZATION",
"        state.cycles += 1",
"        cycle_errors = []",
"        dispatched = 0",
"        try:",
"            execution_results = self.execution_loop.run_bounded_batch(max_dispatches=self.execution_batch_size)",
"            dispatched = sum(1 for r in execution_results if r.dispatched)",
"            state.execution_dispatched += dispatched",
"        except Exception as exc:",
"            state.execution_failures += 1",
"            cycle_errors.append(f'execution:{type(exc).__name__}:{exc}')",
"",
"        # Backpressure: drain executable backlog before adding more goal intake.",
"        if dispatched == 0:",
"            try:",
"                result = self.scheduler.process_next()",
"                if result.processed:",
"                    state.goals_processed += 1",
"                    state.last_orchestration_id = result.orchestration_id",
"                    state.last_reason = result.reason",
"                else:",
"                    state.idle_cycles += 1",
"                    state.last_reason = result.reason",
"            except Exception as exc:",
"                state.scheduler_failures += 1",
"                cycle_errors.append(f'scheduler:{type(exc).__name__}:{exc}')",
"",
"        # CEO failures are isolated from the working execution pump.",
"        try:",
"            ceo_state = self.ceo_runtime.load()",
"            ceo_state = self.ceo_runtime.cycle(ceo_state)",
"            if not ceo_state.ready:",
"                state.ceo_failures += 1",
"                cycle_errors.append(f'ceo:{ceo_state.reason}')",
"        except Exception as exc:",
"            state.ceo_failures += 1",
"            cycle_errors.append(f'ceo:{type(exc).__name__}:{exc}')",
"",
"        state.running = True",
"        state.ready = len(cycle_errors) == 0",
"        if dispatched:",
"            state.last_reason = f'execution_pump_dispatched:{dispatched}'",
"        elif cycle_errors:",
"            state.last_reason = '|'.join(cycle_errors)[:1000]",
"        if any(e.startswith('execution:') for e in cycle_errors):",
"            state.consecutive_failures += 1",
"        else:",
"            state.consecutive_failures = 0",
"        self.save(state)",
"        return state",
"",
]
    s=s[:a]+"\n".join(lines)+"\n"+s[b:]
    p.write_text(s)
print("CONTINUOUS_STABILIZATION_PATCH=PASS")
PY

python -m py_compile "${FILES[@]}"
echo "COMPILE=PASS"

python - <<'PY'
from pathlib import Path
a=Path("companyos/runtime/continuous_goal_runtime.py").read_text()
b=Path("companyos/runtime/autonomous_ceo_runtime_service.py").read_text()
assert "V29_BIG_RUNTIME_STABILIZATION" in a
assert "if dispatched == 0" in a
assert "execution_failures" in a and "scheduler_failures" in a and "ceo_failures" in a
assert "V29_PERSISTENT_CEO_STATE" in b and "def load(self)" in b
print("SOURCE_CONTRACTS=PASS")
PY

echo "===== CONTROLLED ACTIVATION ====="
SUP="$(pgrep -f 'companyos.runtime.service_supervisor' | head -1 || true)"
OLD="$(pgrep -f 'companyos.runtime.continuous_goal_runtime' | tail -1 || true)"
echo "SUPERVISOR_PID=${SUP:-none} OLD_CHILD=${OLD:-none}"
[ -n "${SUP:-}" ] || { echo "ABORT=no_supervisor"; exit 2; }
[ -z "${OLD:-}" ] || kill "$OLD" 2>/dev/null || true
NEW=""
for i in $(seq 1 30); do
 sleep 1
 C="$(pgrep -f 'companyos.runtime.continuous_goal_runtime' | tail -1 || true)"
 if [ -n "${C:-}" ] && [ "$C" != "${OLD:-}" ]; then NEW="$C"; break; fi
 echo "waiting=${i}s"
done
[ -n "${NEW:-}" ] || { echo "ACTIVATION_FAIL"; exit 3; }
echo "NEW_CHILD=$NEW"
echo "ACTIVATION=PASS"

echo "===== 120 SECOND QUALIFICATION ====="
python - <<'PY'
import json,time
from pathlib import Path
from collections import Counter
root=Path.home()/".companyos_runtime"/"task_queue"
def snap():
 c=Counter()
 for p in root.glob("*.json"):
  try:c[str(json.loads(p.read_text()).get("state","UNKNOWN")).upper()]+=1
  except Exception:c["UNREADABLE"]+=1
 return c
a=snap();b=a;print("T+000",dict(a),flush=True)
for sec in range(15,121,15):
 time.sleep(15);b=snap()
 print(f"T+{sec:03d}",dict(b),"completed_delta=",b["COMPLETED"]-a["COMPLETED"],
       "queued_delta=",b["QUEUED"]-a["QUEUED"],"failed_delta=",b["FAILED"]-a["FAILED"],flush=True)
print("FINAL_COMPLETED_DELTA=",b["COMPLETED"]-a["COMPLETED"])
print("FINAL_QUEUED_DELTA=",b["QUEUED"]-a["QUEUED"])
print("FINAL_FAILED_DELTA=",b["FAILED"]-a["FAILED"])
PY

echo "===== HEALTH REPORT ====="
python - <<'PY'
import json
from pathlib import Path
for name in ("continuous_goal_runtime_state.json","autonomous_ceo_runtime_service.json"):
 p=Path.home()/".companyos_runtime"/name
 print("---",name,"---")
 if not p.exists():print("MISSING");continue
 try:
  d=json.loads(p.read_text())
  for k in ("running","ready","last_reason","reason","cycles","cycle_count","consecutive_failures",
            "execution_dispatched","execution_failures","scheduler_failures","ceo_failures","cycles_dispatched_this_tick"):
   if k in d:print(k,"=",d[k])
 except Exception as e:print("READ_ERROR",e)
PY

pgrep -af 'companyos.runtime.service_supervisor' || true
pgrep -af 'companyos.runtime.continuous_goal_runtime' || true
echo "V29_BIG_PUSH_COMPLETE"
echo "QUEUE_RECORDS_DELETED=0"
echo "SUPERVISOR_RESTARTED=NO"
echo "FINANCE_CONNECTORS_CHANGED=NO"
echo "BACKUP=$BACK"
trap - ERR
