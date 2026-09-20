#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
cd "$ROOT"

echo "===== COMPANYOS AUTONOMOUS WORKFORCE IMPORT PATH FIX V3 ====="
echo "Fixes direct scripts/ launcher import path."
echo "No finance mutation. No supervisor restart."

test -f companyos/runtime/autonomous_workforce_loop.py
mkdir -p scripts tests/generated

cat > scripts/companyos_workforce_loop <<'PY'
#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# When launched as:
#   python scripts/companyos_workforce_loop ...
# Python normally places ~/companyos/scripts on sys.path. Explicitly add the
# repository root so the companyos package resolves identically in Termux.
REPO_ROOT = Path(__file__).resolve().parents[1]
repo = str(REPO_ROOT)
if repo not in sys.path:
    sys.path.insert(0, repo)

from companyos.runtime.autonomous_workforce_loop import cycle, run

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["cycle", "run"])
    parser.add_argument("--interval", type=int, default=300)
    args = parser.parse_args()

    if args.command == "cycle":
        print(json.dumps(cycle(), indent=2, default=str))
    else:
        run(args.interval)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
PY
chmod +x scripts/companyos_workforce_loop

cat > tests/generated/test_workforce_launcher_import_v3.py <<'PY'
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "scripts" / "companyos_workforce_loop"

def test_launcher_adds_repo_root_before_companyos_import():
    src = LAUNCHER.read_text()
    assert 'Path(__file__).resolve().parents[1]' in src
    assert 'sys.path.insert(0, repo)' in src
    assert src.index('sys.path.insert(0, repo)') < src.index(
        'from companyos.runtime.autonomous_workforce_loop import cycle, run'
    )

def test_direct_script_can_resolve_companyos_from_outside_repo():
    # Reproduce the failure mode: execute the scripts/ file with cwd outside
    # the repository, but only import/compile it rather than running a live cycle.
    code = f"""
import runpy
p={str(LAUNCHER)!r}
ns=runpy.run_path(p, run_name='companyos_launcher_import_test')
assert callable(ns['cycle'])
assert callable(ns['run'])
"""
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    cp = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(ROOT.parent),
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert cp.returncode == 0, cp.stdout + cp.stderr
PY

echo "===== COMPILE ====="
python -m py_compile scripts/companyos_workforce_loop companyos/runtime/autonomous_workforce_loop.py

echo "===== EXACT IMPORT-PATH REGRESSION TEST ====="
python -m pytest -q tests/generated/test_workforce_launcher_import_v3.py

echo "===== EXISTING WORKFORCE TESTS ====="
python -m pytest -q tests/generated/test_autonomous_workforce_loop_v2.py

echo "===== DIRECT TERMUX-STYLE LIVE CYCLE ====="
# This is intentionally the same file-style invocation that failed previously.
python scripts/companyos_workforce_loop cycle

echo "===== SUPERVISOR PRESERVATION CHECK ====="
python - <<'PY'
import json
from pathlib import Path

paths = [
    Path(".companyos_runtime/service_supervisor_state.json"),
    Path(".companyos_runtime/service_supervisor/state.json"),
]
for p in paths:
    if not p.exists():
        continue
    try:
        d=json.loads(p.read_text())
        print("supervisor_state:", p)
        print("supervisor_pid:", d.get("supervisor_pid"))
        print("running:", d.get("running"))
        print("stop_requested:", d.get("stop_requested"))
        break
    except Exception as e:
        print("supervisor_state_unreadable:", e)
else:
    print("supervisor_state_not_found; supervisor was not modified")
PY

echo "===== COMMIT ONLY FIX FILES ====="
git add scripts/companyos_workforce_loop tests/generated/test_workforce_launcher_import_v3.py
if ! git diff --cached --quiet; then
    git commit -m "fix workforce launcher repository import path" || true
fi

echo "DIRECT_SCRIPT_IMPORT_PATH=FIXED"
echo "FACTORY_CONTRACT_CHANGED=NO"
echo "FINANCE_LIMITS_CHANGED=NO"
echo "SUPERVISOR_RESTARTED=NO"
echo "COMPANYOS_WORKFORCE_IMPORT_PATH_FIX_V3=PASS"
