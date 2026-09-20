#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V64.6 FULL SUITE VERIFY ====="
python -m py_compile companyos/runtime/autonomous_task_queue.py companyos/runtime/adaptive_worker_factory.py companyos/runtime/adaptive_workforce_execution_bridge.py companyos/resilienceops/data_integrity.py
git diff --check
python -m pytest -q tests --disable-warnings --maxfail=1
echo "===== WORKTREE ====="
git status --short
echo "===== DIFF STAT ====="
git diff --stat
echo "V64_6_FULL_SUITE_VERIFY=PASS"
