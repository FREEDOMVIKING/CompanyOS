from pathlib import Path
import json, time, re

ROOT = Path.home()/"companyos"
paths = [
    ROOT/".companyos_runtime/ceo_learning_memory.jsonl",
    ROOT/"companyos_runtime/ceo_learning_memory.jsonl",
    ROOT/".companyos_runtime/companyos_full_autonomy.log",
    ROOT/"companyos_runtime/companyos_full_autonomy.log",
]
cutoff = time.time() - 900
rows = []

for p in paths:
    if not p.exists():
        continue
    try:
        lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()[-2000:]
    except Exception:
        continue
    for line in lines:
        low = line.lower()
        if any(x in low for x in ("reasoning_http_error", "more credits", "fewer max_tokens", '"status_code": 502', "partial_cycle_errors")):
            rows.append({"source": str(p.relative_to(ROOT)), "line": line[:5000]})

print(json.dumps({
    "matching_recent_tail_entries": len(rows),
    "entries": rows[-60:],
}, indent=2))
