#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V64.2 FULL SUITE VERIFY ====="
echo "BRANCH=$(git branch --show-current)"
python -m py_compile companyos/runtime/autonomous_task_queue.py companyos/runtime/adaptive_worker_factory.py
git diff --check
echo "===== FULL PYTEST ====="
python -m pytest -q tests --disable-warnings --maxfail=1
echo "===== CHANGED FILES ====="
git status --short
echo "===== DIFF STAT ====="
git diff --stat
echo "V64_2_FULL_SUITE_VERIFY=PASS"
