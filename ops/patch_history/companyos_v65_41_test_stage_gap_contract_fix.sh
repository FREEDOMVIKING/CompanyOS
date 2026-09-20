#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.41 TEST_STAGE GAP CONTRACT FIX ====="
TARGET="companyos/runtime/capability_expansion.py"
BACKUP="$TARGET.v65_41_backup_$(date +%s)"
cp "$TARGET" "$BACKUP"
echo "BACKUP=$BACKUP"

python - <<'PY'
from pathlib import Path
import re, py_compile

p=Path("companyos/runtime/capability_expansion.py")
s=p.read_text()

# V65.40 proved test_stage receives a gap dict but line 319 treats it as a string:
# root / module_path / test_root / test_path
# Normalize the public gap argument once, without changing stage_plan's contract.
m=re.search(r'(?m)^def test_stage\(([^)]*)\):\n', s)
if not m:
    raise SystemExit("ABORT=test_stage definition not found")

start=m.end()
indent="    "
patch=(
    f'{indent}# V65.41: normalize gap object to canonical capability id.\n'
    f'{indent}gap_id = gap.get("id") if isinstance(gap, dict) else str(gap)\n'
)
# Avoid duplicate patch.
window=s[start:start+500]
if "gap_id = gap.get" not in window:
    s=s[:start]+patch+s[start:]

# Inside test_stage only, replace canonical_paths(gap) with canonical_paths(gap_id).
next_def=re.search(r'(?m)^def \w+\(', s[start+len(patch):])
end=(start+len(patch)+next_def.start()) if next_def else len(s)
head=s[:start]
body=s[start:end]
tail=s[end:]
body=body.replace("canonical_paths(gap)", "canonical_paths(gap_id)")
s=head+body+tail

p.write_text(s)
py_compile.compile(str(p), doraise=True)
print("PATCH_COMPILE=PASS")
PY

echo "===== TARGETED TEST ====="
if python -m pytest -q tests/test_capability_expansion_test_recovery_v5.py; then
  echo "V65_41_TARGETED_TEST=PASS"
else
  echo "V65_41_TARGETED_TEST=FAIL"
  echo "RESTORING_BACKUP"
  cp "$BACKUP" "$TARGET"
  python -m py_compile "$TARGET"
  echo "RESTORE_COMPILE=PASS"
  exit 1
fi

echo "V65_41_COMPLETE"
