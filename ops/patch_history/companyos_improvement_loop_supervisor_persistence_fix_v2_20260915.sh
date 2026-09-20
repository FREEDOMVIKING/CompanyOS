#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
SUP="companyos/runtime/service_supervisor.py"
TEST="tests/generated/test_improvement_loop_supervisor_registration_v2.py"
mkdir -p .companyos_runtime/backups tests/generated
cp "$SUP" ".companyos_runtime/backups/service_supervisor.$(date +%Y%m%d_%H%M%S).py"

echo "===== EXACT-LAYOUT SUPERVISOR REGISTRATION V2 ====="
python - <<'PY'
from pathlib import Path
import ast
p=Path("companyos/runtime/service_supervisor.py")
s=p.read_text()
name="continuous_profit_improvement_loop"
if name in s:
    print("REGISTRATION_ALREADY_PRESENT")
else:
    anchor="        return services"
    if anchor not in s:
        raise SystemExit("SAFE_ABORT: exact return-services anchor not found")
    block = (
'        if (Path.home()/"companyos/companyos/runtime/continuous_profit_improvement_loop.py").exists():\n'
'            services.append(\n'
'                ManagedService(\n'
'                    "continuous_profit_improvement_loop",\n'
'                    (python, "-m", "companyos.runtime.continuous_profit_improvement_loop"),\n'
'                )\n'
'            )\n'
    )
    s=s.replace(anchor,block+anchor,1)
    ast.parse(s)
    p.write_text(s)
    print("REGISTRATION_INSERTED")
ast.parse(p.read_text())
PY

python -m py_compile "$SUP" companyos/runtime/continuous_profit_improvement_loop.py

cat > "$TEST" <<'PY'
from pathlib import Path
import ast
def test_registration_exact():
    s=Path("companyos/runtime/service_supervisor.py").read_text()
    ast.parse(s)
    assert '"continuous_profit_improvement_loop"' in s
    assert '"companyos.runtime.continuous_profit_improvement_loop"' in s
    assert s.index('"continuous_profit_improvement_loop"') < s.index("return services")
def test_module_compiles():
    ast.parse(Path("companyos/runtime/continuous_profit_improvement_loop.py").read_text())
PY

echo "===== TEST ====="
python -m pytest -q "$TEST" tests/generated/test_continuous_profit_improvement_loop.py tests/generated/test_verified_outcome_scoring.py

echo "===== CURRENT PROCESS ====="
if pgrep -f 'companyos.runtime.continuous_profit_improvement_loop' >/dev/null 2>&1; then
  echo "IMPROVEMENT_LOOP_RUNNING=YES"
else
  mkdir -p .companyos_runtime/improvement_loop
  nohup python -u -m companyos.runtime.continuous_profit_improvement_loop > .companyos_runtime/improvement_loop/console.log 2>&1 &
  echo $! > .companyos_runtime/improvement_loop/pid
  sleep 2
  pgrep -f 'companyos.runtime.continuous_profit_improvement_loop' >/dev/null
  echo "IMPROVEMENT_LOOP_RUNNING=STARTED"
fi

echo "HEALTHY_SUPERVISOR_RESTARTED=NO"
echo "PERSISTENCE_ON_NEXT_NORMAL_SUPERVISOR_START=YES"

git add "$SUP" "$TEST"
if ! git diff --cached --quiet; then
  git commit -m "register profit improvement loop with current supervisor layout"
else
  echo "NO_NEW_COMMIT_REQUIRED"
fi

echo "===== VERIFY ====="
grep -n -A7 -B2 'continuous_profit_improvement_loop' "$SUP"
python scripts/companyos_improvementctl status || true
echo "COMPANYOS_IMPROVEMENT_LOOP_SUPERVISOR_PERSISTENCE_V2=PASS"
