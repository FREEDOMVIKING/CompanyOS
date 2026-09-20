#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V65.2 RESTORE PHASE 285 TEST ====="
T="tests/test_phase285_292.py"
cp "$T" "$T.v65_2_backup_$(date +%Y%m%d_%H%M%S)"
cat > "$T" <<'PY'
from companyos_phase285_292 import ImprovementStateStore, PausePolicy, ResumeController

def test_state_store(tmp_path):
    s = ImprovementStateStore(tmp_path)
    state = s.load()
    state["cycles_completed"] = 1
    s.save(state)
    assert s.load()["cycles_completed"] == 1

def test_pause_policy():
    assert PausePolicy().evaluate({"paused": True}, {})["pause"] is True

def test_resume_controller(tmp_path):
    ctl = ResumeController(tmp_path)
    ctl.pause()
    assert ctl.status()["paused"] is True
    ctl.resume()
    assert ctl.status()["paused"] is False
PY
python -m py_compile "$T"
python -m pytest -q "$T" --disable-warnings --maxfail=1
git diff --check
echo "V65_2_PHASE285_TEST=PASS"
echo "===== NEXT FULL-SUITE FAILURE ====="
python -m pytest -q tests --disable-warnings --maxfail=1
echo "V65_2_FULL_SUITE=PASS"
