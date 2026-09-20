#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V64 VERIFY + COMMIT + PUSH ====="

BRANCH="$(git branch --show-current)"
echo "BRANCH=$BRANCH"
[ "$BRANCH" = "companyos-continuous-fix-2026-09-11" ] || { echo "V64_ABORT=unexpected branch"; exit 2; }

F="companyos/runtime/autonomous_task_queue.py"
python -m py_compile "$F"
grep -q 'durable_task_projection_missing' "$F" || { echo "V64_ABORT=V62 guard missing"; exit 3; }

echo "===== TARGETED TESTS ====="
if [ -d tests ]; then
  python -m pytest -q tests --disable-warnings --maxfail=1
else
  echo "NO_TEST_DIRECTORY=1"
fi

echo "===== DIFF ====="
git diff --check
git diff -- "$F" | sed -n '1,180p'

# Stage only the intended root-cause source fix.
git add -- "$F"
echo "===== STAGED ====="
git diff --cached --check
git diff --cached --stat
git diff --cached -- "$F" | sed -n '1,180p'

if git diff --cached --quiet; then
  echo "V64_ABORT=nothing staged"
  exit 4
fi

git commit -m "fix(queue): block duplicate enqueue when durable projection is missing"
git push origin "$BRANCH"

echo "COMMIT=$(git rev-parse HEAD)"
echo "REMOTE=$(git remote get-url origin)"
echo "WORKTREE_STATUS:"
git status --short
echo "V64_VERIFY_COMMIT_PUSH=PASS"
