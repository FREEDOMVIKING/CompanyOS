#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"

echo "===== COMPANYOS ADAPTIVE WORKER FACTORY IMPORT FIX ====="
echo "No supervisor restart. No finance changes."

test -f companyos/runtime/adaptive_worker_factory.py || {
  echo "ERROR: adaptive_worker_factory.py missing"
  exit 1
}

cp scripts/companyos_workerctl ".companyos_runtime/companyos_workerctl.before_import_fix.$(date +%s).bak"

cat > scripts/companyos_workerctl <<'PY'
#!/data/data/com.termux/files/usr/bin/python
from pathlib import Path
import json
import sys

ROOT = Path.home() / "companyos"
root_s = str(ROOT)
if root_s not in sys.path:
    sys.path.insert(0, root_s)

from companyos.runtime.adaptive_worker_factory import Factory

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "cycle":
        print(json.dumps(Factory().cycle(), indent=2))
        return 0

    p = ROOT / ".companyos_runtime/adaptive_workers/latest.json"
    print(p.read_text() if p.exists() else json.dumps({"status": "not_run"}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
PY
chmod +x scripts/companyos_workerctl

echo "===== IMPORT CHECK ====="
python - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home()/"companyos"))
from companyos.runtime.adaptive_worker_factory import Factory
print("ADAPTIVE_WORKER_FACTORY_IMPORT=PASS")
PY

echo "===== COMPILE ====="
python -m py_compile \
  companyos/runtime/adaptive_worker_factory.py \
  scripts/companyos_workerctl \
  companyos/runtime/service_supervisor.py
echo "COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/generated/test_adaptive_worker_factory.py

echo "===== FIRST REAL CYCLE ====="
python scripts/companyos_workerctl cycle

echo "===== STATUS ====="
python scripts/companyos_workerctl

echo "===== SUPERVISOR REGISTRATION CHECK ====="
if grep -q 'adaptive_worker_factory' companyos/runtime/service_supervisor.py; then
  echo "SUPERVISOR_REGISTRATION=PASS"
else
  echo "SUPERVISOR_REGISTRATION=MISSING"
  exit 1
fi

echo "===== COMMIT ONLY FIX ====="
git add scripts/companyos_workerctl companyos/runtime/adaptive_worker_factory.py \
  tests/generated/test_adaptive_worker_factory.py companyos/runtime/service_supervisor.py
git commit -m "fix adaptive worker factory launcher import path" || true

echo "HEALTHY_SUPERVISOR_RESTARTED=NO"
echo "FINANCE_LIMITS_CHANGED=NO"
echo "COMPANYOS_ADAPTIVE_WORKER_FACTORY_IMPORT_FIX=PASS"
