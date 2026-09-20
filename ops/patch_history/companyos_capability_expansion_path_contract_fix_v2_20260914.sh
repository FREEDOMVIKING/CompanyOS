#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
BACKUP="$HOME/companyos_backups/capability_expansion_path_fix_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP"

ENGINE="companyos/runtime/capability_expansion.py"
[ -f "$ENGINE" ] || { echo "ERROR: $ENGINE not found"; exit 1; }
cp -a "$ENGINE" "$BACKUP/"

python - <<'PY'
from pathlib import Path
import re

p = Path("companyos/runtime/capability_expansion.py")
s = p.read_text()

# Normalize generated file declarations before validation.  The expansion
# sandbox remains restricted to these two exact roots.
marker = "COMPANYOS_PATH_CONTRACT_V2"
if marker not in s:
    insert_after = None

    # Put helpers before the first class, or after imports if no class exists.
    m = re.search(r'(?m)^class\s+\w+', s)
    pos = m.start() if m else 0

    helper = r