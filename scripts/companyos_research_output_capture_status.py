import json
from pathlib import Path

ROOT = Path.home() / "companyos"
raw = ROOT / ".companyos_runtime" / "canonical_research_outputs"
state = ROOT / ".companyos_runtime" / "research_output_capture_state.json"

files = sorted(raw.glob("*.json")) if raw.exists() else []
try:
    st = json.loads(state.read_text(encoding="utf-8"))
except Exception:
    st = {}

print(json.dumps({
    "capture_file_count": len(files),
    "latest_capture_files": [str(p.relative_to(ROOT)) for p in files[-20:]],
    "capture_state": st,
}, indent=2, default=str))
