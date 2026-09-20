#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${HOME}/companyos"
SOURCE_BRANCH="companyos-continuous-fix-2026-09-11"

cd "$ROOT"

echo "===== COMPANYOS MAIN PROMOTION ====="
git fetch origin --prune

CURRENT="$(git branch --show-current)"
if [ "$CURRENT" != "$SOURCE_BRANCH" ]; then
  echo "ERROR: current branch is '$CURRENT'"
  echo "Expected: '$SOURCE_BRANCH'"
  exit 2
fi

LOCAL_HEAD="$(git rev-parse HEAD)"
REMOTE_HEAD="$(git rev-parse "origin/$SOURCE_BRANCH")"
MAIN_HEAD="$(git rev-parse origin/main)"

echo "local source:  $LOCAL_HEAD"
echo "remote source: $REMOTE_HEAD"
echo "current main:  $MAIN_HEAD"

if [ "$LOCAL_HEAD" != "$REMOTE_HEAD" ]; then
  echo "ERROR: local source branch is not identical to the branch already pushed to GitHub."
  echo "Push the source branch first, then rerun."
  exit 3
fi

if ! git merge-base --is-ancestor origin/main HEAD; then
  echo "ERROR: main is not an ancestor of the source branch."
  echo "Refusing non-fast-forward promotion."
  exit 4
fi

AHEAD="$(git rev-list --count origin/main..HEAD)"
BEHIND="$(git rev-list --count HEAD..origin/main)"

echo "ahead of main: $AHEAD"
echo "behind main:   $BEHIND"

if [ "$BEHIND" != "0" ]; then
  echo "ERROR: source branch is behind main. Refusing promotion."
  exit 5
fi

echo
echo "===== PUSHING FULL COMPANYOS TO MAIN ====="
git push origin HEAD:main

echo
echo "===== VERIFYING GITHUB MAIN ====="
git fetch origin main
NEW_MAIN="$(git rev-parse origin/main)"

if [ "$NEW_MAIN" != "$LOCAL_HEAD" ]; then
  echo "ERROR: verification failed."
  echo "origin/main: $NEW_MAIN"
  echo "expected:    $LOCAL_HEAD"
  exit 6
fi

echo "origin/main now points to:"
git log -1 --oneline origin/main

echo
echo "COMPANYOS_MAIN_PROMOTION=PASS"
