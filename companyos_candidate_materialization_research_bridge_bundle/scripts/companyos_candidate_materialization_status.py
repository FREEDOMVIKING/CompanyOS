import json
from pathlib import Path
from companyos.strategy.candidate_materialization_bridge import ROOT, STATE_PATH, REPORT_PATH, load_json

candidate_dir = ROOT / ".companyos_runtime" / "profit_first_candidates"
files = sorted(candidate_dir.glob("*.json")) if candidate_dir.exists() else []

print(json.dumps({
    "candidate_file_count": len(files),
    "candidate_files": [str(p.relative_to(ROOT)) for p in files[:50]],
    "bridge_state": load_json(STATE_PATH, {}),
    "materialization_report": load_json(REPORT_PATH, {}),
}, indent=2, default=str))
