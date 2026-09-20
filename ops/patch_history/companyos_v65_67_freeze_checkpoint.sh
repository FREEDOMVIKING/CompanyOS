#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export GIT_PAGER=cat
export PAGER=cat

STAMP="$(date +%Y%m%d_%H%M%S)"
CPROOT="$HOME/.companyos_runtime/checkpoints/v65_66_clean_$STAMP"
mkdir -p "$CPROOT"

echo "===== COMPANYOS V65.67 FREEZE CHECKPOINT ====="
echo "CHECKPOINT_DIR=$CPROOT"

# Record git identity/state without changing it.
git rev-parse --show-toplevel > "$CPROOT/git_root.txt" 2>/dev/null || true
git rev-parse --abbrev-ref HEAD > "$CPROOT/git_branch.txt" 2>/dev/null || true
git rev-parse HEAD > "$CPROOT/git_head.txt" 2>/dev/null || true
git status --short > "$CPROOT/git_status_short.txt" 2>/dev/null || true
git status > "$CPROOT/git_status.txt" 2>/dev/null || true
git diff > "$CPROOT/uncommitted.patch" 2>/dev/null || true
git diff --cached > "$CPROOT/staged.patch" 2>/dev/null || true

echo "GIT_BRANCH=$(cat "$CPROOT/git_branch.txt" 2>/dev/null || echo unknown)"
echo "GIT_HEAD=$(cat "$CPROOT/git_head.txt" 2>/dev/null || echo unknown)"

echo "===== VERIFY CLEAN TEST BASELINE ====="
python -m pytest -q | tee "$CPROOT/pytest_full.txt"
grep -E '[0-9]+ passed' "$CPROOT/pytest_full.txt" | tail -1 > "$CPROOT/pytest_summary.txt" || true
echo "PYTEST_SUMMARY=$(cat "$CPROOT/pytest_summary.txt" 2>/dev/null || echo unavailable)"

# Save the most recently modified source/test files that participated in the repair.
mkdir -p "$CPROOT/files"
for f in \
  companyos/runtime/capability_expansion.py \
  companyos/runtime/execution_drain_engine.py \
  companyos/runtime/autonomous_task_dispatcher.py \
  companyos/resilienceops/data_integrity.py \
  companyos/modules/phase18601_19000/autonomous_operations_kernel.py \
  companyos/walletintegration/receipt_verifier.py \
  tests/test_phase18601_19000.py \
  tests/test_phase38001_40000.py
do
  if [ -f "$f" ]; then
    mkdir -p "$CPROOT/files/$(dirname "$f")"
    cp -p "$f" "$CPROOT/files/$f"
    echo "SNAPSHOT_FILE=$f"
  fi
done

# Save a compact manifest with hashes.
(
  cd "$CPROOT/files"
  find . -type f -print0 | sort -z | xargs -0 sha256sum
) > "$CPROOT/sha256_manifest.txt" 2>/dev/null || true

cat > "$CPROOT/CHECKPOINT.txt" <<EOF
CompanyOS checkpoint
Version: V65.66 clean baseline
Created: $(date -Iseconds)
Repository: $HOME/companyos
Branch: $(cat "$CPROOT/git_branch.txt" 2>/dev/null || echo unknown)
Head: $(cat "$CPROOT/git_head.txt" 2>/dev/null || echo unknown)
Pytest: $(cat "$CPROOT/pytest_summary.txt" 2>/dev/null || echo unavailable)

Purpose:
Freeze the first known-good state after the V65.66 repair series before runtime validation.

Notes:
- This checkpoint does not modify git history.
- uncommitted.patch captures tracked working-tree edits.
- staged.patch captures staged edits if any.
- files/ contains direct snapshots of the key repaired modules/tests.
EOF

ARCHIVE="$HOME/.companyos_runtime/checkpoints/companyos_v65_66_clean_$STAMP.tar.gz"
tar -C "$(dirname "$CPROOT")" -czf "$ARCHIVE" "$(basename "$CPROOT")"

echo "ARCHIVE=$ARCHIVE"

# Also place a copy in Downloads when Android shared storage is available.
DL="$HOME/storage/downloads"
if [ -d "$DL" ]; then
  cp -f "$ARCHIVE" "$DL/"
  echo "DOWNLOAD_COPY=$DL/$(basename "$ARCHIVE")"
fi

echo "===== CHECKPOINT VERIFY ====="
tar -tzf "$ARCHIVE" >/dev/null
echo "ARCHIVE_VERIFY=PASS"

echo "V65_67_CHECKPOINT=PASS"
