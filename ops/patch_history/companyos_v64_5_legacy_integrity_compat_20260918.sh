#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V64.5 LEGACY INTEGRITY COMPAT ====="
F="companyos/resilienceops/data_integrity.py"
cp "$F" "$F.v64_5_backup_$(date +%Y%m%d_%H%M%S)"
cat >> "$F" <<'PY'

# Legacy compatibility names retained for older phase tests/importers.
# They delegate to the current deterministic validation implementation.
class DataIntegrityGuard:
    @staticmethod
    def validate(items):
        return validate_work_items(items)

    @staticmethod
    def check(items):
        return check_integrity(items)


def data_integrity(items):
    return validate_work_items(items)
PY
python -m py_compile "$F"
python - <<'PY'
from companyos.resilienceops.data_integrity import DataIntegrityGuard, data_integrity
x=[{"id":"x","title":"x","status":"ready"}]
assert DataIntegrityGuard.validate(x)["valid"] is True
assert DataIntegrityGuard.check(x)["valid"] is True
assert data_integrity(x)["valid"] is True
print("COMPAT_IMPORTS_AND_DELEGATION=PASS")
PY
git diff --check
echo "V64_5_LEGACY_INTEGRITY_COMPAT=PASS"
