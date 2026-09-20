#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"
cd "$ROOT"
PY="${PREFIX:-/data/data/com.termux/files/usr}/bin/python"
[ -x "$PY" ] || PY=python

echo "===== COMPANYOS WORKFORCE EXECUTION BRIDGE V3 ====="
echo "Fixes launcher import path; preserves Factory.cycle integration."
echo "No finance/DNS mutation. No supervisor restart."

mkdir -p .companyos_runtime/backups
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
[ -f scripts/companyos_workforce_execute ] && cp scripts/companyos_workforce_execute ".companyos_runtime/backups/companyos_workforce_execute.$STAMP.bak"

cat > scripts/companyos_workforce_execute <<'PYCODE'
#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
import json
import sys
from pathlib import Path

# Resolve ~/companyos regardless of the caller's working directory.
REPO = Path(__file__).resolve().parents[1]
repo_s = str(REPO)
if repo_s not in sys.path:
    sys.path.insert(0, repo_s)

from companyos.runtime.adaptive_workforce_execution_bridge import cycle

if __name__ == "__main__":
    print(json.dumps(cycle(), indent=2, default=str))
PYCODE
chmod +x scripts/companyos_workforce_execute

mkdir -p tests/generated
cat > tests/generated/test_workforce_launcher_v3.py <<'PYCODE'
from pathlib import Path

def test_launcher_bootstraps_repo_path():
    p=Path("scripts/companyos_workforce_execute")
    s=p.read_text()
    assert "Path(__file__).resolve().parents[1]" in s
    assert "sys.path.insert(0, repo_s)" in s

def test_bridge_uses_factory_cycle():
    p=Path("companyos/runtime/adaptive_workforce_execution_bridge.py")
    s=p.read_text()
    assert "factory.cycle" in s
    assert "factory.evaluate" not in s
PYCODE

echo "===== COMPILE ====="
"$PY" -m py_compile scripts/companyos_workforce_execute companyos/runtime/adaptive_workforce_execution_bridge.py

echo "===== TEST ====="
"$PY" -m pytest -q \
  tests/generated/test_workforce_launcher_v3.py \
  tests/generated/test_adaptive_workforce_execution_bridge_v2.py

echo "===== IMPORT TEST FROM OUTSIDE REPO ====="
(
  cd "$HOME"
  "$PY" "$ROOT/scripts/companyos_workforce_execute"
)

echo "===== MODULE-MODE LIVE CYCLE ====="
PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" \
  "$PY" -m companyos.runtime.adaptive_workforce_execution_bridge

echo "===== STATE ====="
"$PY" - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos/.companyos_runtime/adaptive_workforce_execution_bridge_state.json"
d=json.loads(p.read_text())
print(json.dumps(d, indent=2))
assert d.get("factory_cycle_called") is True, d
assert not d.get("error"), d
print("FACTORY_CYCLE_LIVE=YES")
PY

echo "===== SUPERVISOR UNTOUCHED CHECK ====="
"$PY" - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos/.companyos_runtime/service_supervisor_state.json"
try:
    d=json.loads(p.read_text())
    print("supervisor_pid:", d.get("supervisor_pid"))
    print("running:", d.get("running"))
    print("stop_requested:", d.get("stop_requested"))
except Exception as e:
    print("supervisor_state_read:", type(e).__name__)
PY

echo "===== COMMIT ONLY V3 ====="
git add -- scripts/companyos_workforce_execute tests/generated/test_workforce_launcher_v3.py
if ! git diff --cached --quiet; then
  git commit -m "fix adaptive workforce launcher repository import path"
else
  echo "No staged changes."
fi

echo "HEALTHY_SUPERVISOR_RESTARTED=NO"
echo "FINANCE_LIMITS_CHANGED=NO"
echo "WORKFORCE_LAUNCHER_IMPORT_PATH_FIXED=YES"
echo "FACTORY_CYCLE_LIVE=YES"
echo "COMPANYOS_ADAPTIVE_WORKFORCE_EXECUTION_BRIDGE_V3=PASS"
