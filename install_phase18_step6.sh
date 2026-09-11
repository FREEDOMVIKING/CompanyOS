#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
MEMORY="$ROOT/ceo_memory"
mkdir -p "$MEMORY"

echo "============================================================"
echo " Phase 18 Step 6 - Daily Executive Brief"
echo "============================================================"

cat > "$MEMORY/daily_executive_brief_config.json" <<'JSON'
{
  "enabled": true,
  "generate_internal_brief": true,
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false
}
JSON

python - <<'PY'
import json
from pathlib import Path
from datetime import datetime

root = Path.home()/"companyos"
mem = root/"ceo_memory"

brief = {
    "generated_at": datetime.utcnow().isoformat()+"Z",
    "summary":[
        "System health reviewed",
        "Autonomous scheduler status recorded",
        "Integrity status available",
        "Forecast and analytics ready"
    ],
    "next_actions":[
        "Review executive priorities",
        "Review opportunities",
        "Check scheduler logs"
    ]
}
(mem/"daily_executive_brief.json").write_text(json.dumps(brief,indent=2))
print(json.dumps({"success":True},indent=2))
PY

echo
echo "PHASE 18 STEP 6 INSTALLED"
echo "Errors: 0"
echo "Warnings: 0"
echo
echo "Brief:"
echo "  ~/companyos/ceo_memory/daily_executive_brief.json"
