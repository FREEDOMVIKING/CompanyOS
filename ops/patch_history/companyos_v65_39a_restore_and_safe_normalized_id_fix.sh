#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD"
echo "===== V65.39A RESTORE + SAFE NORMALIZED-ID FIX ====="

TARGET="companyos/runtime/capability_expansion.py"
BACKUP="$(ls -1t companyos/runtime/capability_expansion.py.v65_39_backup_* 2>/dev/null | head -n1 || true)"
if [ -z "$BACKUP" ]; then
  echo "V65_39A_ABORT=no_v65_39_backup_found"; exit 1
fi
echo "RESTORING_FROM=$BACKUP"
cp "$BACKUP" "$TARGET"

python -m py_compile "$TARGET"
echo "RESTORE_COMPILE=PASS"

python - <<'PY'
from pathlib import Path
import re, py_compile
p=Path("companyos/runtime/capability_expansion.py")
src=p.read_text()
start=src.index("def test_stage(")
m=re.search(r"\ndef [A-Za-z_]\w*\(",src[start+1:])
end=start+1+m.start() if m else len(src)
old=src[start:end]

# Preserve the function's existing indentation/signature. Only normalize the
# argument at canonical_paths() call sites inside test_stage.
new=re.sub(
    r"canonical_paths\((gap_id|cid)\)",
    r"canonical_paths(normalize_capability_id(\1))",
    old
)
if new == old:
    if "canonical_paths(normalize_capability_id(" in old:
        print("PATCH_STATUS=already_correct")
    else:
        print("TEST_STAGE_BLOCK_BEGIN"); print(old); print("TEST_STAGE_BLOCK_END")
        raise SystemExit("V65_39A_ABORT=no_safe_callsite_match")
else:
    p.write_text(src[:start]+new+src[end:])
    print("PATCH_STATUS=safe_expression_patch")

py_compile.compile(str(p),doraise=True)
print("PATCH_COMPILE=PASS")
PY

echo "===== TARGETED TEST ====="
python -m pytest -q tests/test_capability_expansion_test_recovery_v5.py
echo "V65_39A_FIX=PASS"
