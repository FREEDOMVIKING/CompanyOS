#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
cd "$ROOT"

latest="$(ls -1dt "$RT"/audit_logs/* 2>/dev/null | head -1 || true)"
if [ -z "$latest" ]; then
  echo "AUDIT_FORENSICS_ABORT=no_audit_log_directory"
  exit 1
fi

echo "===== COMPANYOS AUDIT FAILURE FORENSICS ====="
echo "LOG_DIR=$latest"
echo "NOTE=READ_ONLY"
echo

show_log () {
  name="$1"
  file="$latest/$name.log"
  echo "===== $name ====="
  if [ ! -f "$file" ]; then
    echo "STATUS=LOG_NOT_FOUND"
    echo
    return
  fi
  echo "LOG=$file"
  echo "--- failure/error lines ---"
  grep -Ein 'FAILED|FAILURE|ERROR|Error|Traceback|AssertionError|ImportError|ModuleNotFoundError|timeout|not found|unhealthy|blocked|missing|required|abort' "$file" | tail -n 120 || true
  echo "--- final 120 lines ---"
  tail -n 120 "$file" || true
  echo
}

show_log pytest_full
show_log native_full_launch_validation
show_log native_launch_audit
show_log native_qualify
show_log native_company_health

echo "===== PYTEST FAILURE NAMES ONLY ====="
if [ -f "$latest/pytest_full.log" ]; then
  grep -E '^(FAILED|ERROR) ' "$latest/pytest_full.log" | tail -n 100 || true
fi

echo
echo "===== CURRENT GIT STATE ====="
git --no-pager status --short
echo "HEAD=$(git rev-parse HEAD)"
echo "BRANCH=$(git branch --show-current)"

echo
echo "COMPANYOS_AUDIT_FAILURE_FORENSICS=COMPLETE"
