#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.42 SAFE TEST_STAGE FUNCTION REWRITE ====="
TARGET="companyos/runtime/capability_expansion.py"
BACKUP="$TARGET.v65_42_backup_$(date +%s)"
cp "$TARGET" "$BACKUP"
echo "BACKUP=$BACKUP"

# First prove current file is healthy. V65.41 failed during compile before its
# test, so its shell script never reached its own restore branch.
python -m py_compile "$TARGET" || {
  echo "CURRENT_FILE_NOT_COMPILEABLE=restoring_latest_known_compileable_backup"
  LATEST="$(ls -1t "$TARGET".v65_41_backup_* "$TARGET".v65_39_backup_* 2>/dev/null | head -n1 || true)"
  test -n "$LATEST" || { echo "ABORT=no suitable backup found"; exit 1; }
  cp "$LATEST" "$TARGET"
  python -m py_compile "$TARGET"
  echo "BASELINE_RESTORE=PASS:$LATEST"
}

python - <<'PY'
from pathlib import Path
import ast, py_compile

p=Path("companyos/runtime/capability_expansion.py")
s=p.read_text()
tree=ast.parse(s)

node=None
for n in tree.body:
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name=="test_stage":
        node=n
        break
if node is None:
    raise SystemExit("ABORT=test_stage not found")

lines=s.splitlines(keepends=True)
start=node.lineno-1
end=node.end_lineno

old="".join(lines[start:end])
print("OLD_TEST_STAGE_BEGIN")
print(old)
print("OLD_TEST_STAGE_END")

# Surgical semantic repair: preserve the function body/indentation exactly,
# but normalize only the path-expression operands inside this function.
new=old
anchor = "def test_stage("
first_nl = new.find("\n")
if first_nl < 0:
    raise SystemExit("ABORT=malformed test_stage")

insertion='    gap_id = gap.get("id") if isinstance(gap, dict) else str(gap)\n'
if "gap_id = gap.get" not in new:
    new=new[:first_nl+1]+insertion+new[first_nl+1:]

# The V65.40 traceback proved module_path is a dict at the '/' expression.
# canonical_paths() returns path strings keyed by module/test, so normalize
# those values before Path arithmetic without altering the caller contract.
new=new.replace(
    "root/module_path/test_root/test_path",
    "root/str(module_path)/str(test_root)/str(test_path)"
)
new=new.replace(
    "root / module_path / test_root / test_path",
    "root / str(module_path) / str(test_root) / str(test_path)"
)

# Also normalize canonical_paths input if this function passes the whole gap.
new=new.replace("canonical_paths(gap)", "canonical_paths(gap_id)")

lines[start:end]=[new]
p.write_text("".join(lines))
py_compile.compile(str(p), doraise=True)
print("PATCH_COMPILE=PASS")
PY

echo "===== TARGETED RECOVERY TEST ====="
set +e
python -m pytest -q tests/test_capability_expansion_test_recovery_v5.py
RC=$?
set -e

if [ "$RC" -ne 0 ]; then
  echo "V65_42_TARGETED_TEST=FAIL"
  cp "$BACKUP" "$TARGET"
  python -m py_compile "$TARGET"
  echo "AUTO_RESTORE=PASS"
  exit "$RC"
fi

echo "V65_42_TARGETED_TEST=PASS"
echo "V65_42_COMPLETE"
