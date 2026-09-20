#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.72 PROFIT OBJECTIVE HARD-CODE AUDIT ====="
echo "SOURCE_WRITES=0"
echo "QUEUE_WRITES=0"

python - <<'PY'
from pathlib import Path
import json, re
from collections import Counter

ROOT = Path.home() / "companyos"
RUNTIME = Path.home() / ".companyos_runtime"
QUEUE = RUNTIME / "task_queue"

profit_terms = re.compile(
    r"(primary economic directive|maximi[sz]e.{0,80}profit|profitability|expected[_ ]profit|net profit|risk[- ]adjusted|enterprise value|expected roi|return on investment)",
    re.I | re.S,
)

# ---- Production source audit ----
matches = []
scanned = 0

for p in sorted((ROOT / "companyos").rglob("*.py")):
    name = p.name.lower()
    ps = str(p).lower()
    if (
        "backup" in name
        or ".bak" in name
        or ".v65_" in name
        or "__pycache__" in ps
    ):
        continue

    try:
        txt = p.read_text(errors="ignore")
    except Exception:
        continue

    scanned += 1
    found = list(profit_terms.finditer(txt))
    if found:
        snippets = []
        for m in found[:6]:
            lo = max(0, m.start() - 120)
            hi = min(len(txt), m.end() + 220)
            snippets.append(" ".join(txt[lo:hi].split()))
        matches.append((p, len(found), snippets))

print("SOURCE_FILES_SCANNED=", scanned)
print("SOURCE_FILES_WITH_PROFIT_OBJECTIVE=", len(matches))

for p, count, snippets in sorted(matches, key=lambda x: (-x[1], str(x[0])))[:40]:
    print("SOURCE_MATCH_FILE=", p.relative_to(ROOT), "MATCHES=", count)
    for s in snippets[:3]:
        print("  SNIPPET=", s[:700])

# Stronger check for an explicit governing directive, not a random use of "profit".
explicit_files = []
for p, _, _ in matches:
    txt = p.read_text(errors="ignore")
    low = txt.lower()
    if (
        "primary economic directive" in low
        or ("maximize" in low and "profit" in low)
        or ("maximise" in low and "profit" in low)
    ):
        explicit_files.append(str(p.relative_to(ROOT)))

print("EXPLICIT_GOVERNING_DIRECTIVE_FILES=", explicit_files)

# ---- Current production queue propagation audit ----
counts = Counter()
missing_samples = []
present_samples = []

if QUEUE.exists():
    for p in sorted(QUEUE.glob("*.json")):
        try:
            d = json.loads(p.read_text(errors="ignore"))
        except Exception:
            counts["unreadable"] += 1
            continue

        state = str(d.get("state") or "UNKNOWN")
        if state != "QUEUED":
            continue

        payload = d.get("payload")
        if not isinstance(payload, dict):
            counts["queued_non_dict_payload"] += 1
            continue

        stage = str(payload.get("stage") or "")
        task_type = str(d.get("task_type") or "")
        text = json.dumps(payload, sort_keys=True, default=str)

        counts["queued_total"] += 1
        counts[f"type_{task_type}"] += 1
        if stage:
            counts[f"stage_{stage}"] += 1

        if profit_terms.search(text):
            counts["queued_profit_objective_present"] += 1
            if len(present_samples) < 8:
                present_samples.append({
                    "task_id": d.get("task_id"),
                    "task_type": task_type,
                    "stage": stage,
                    "goal_id": payload.get("goal_id"),
                })
        else:
            counts["queued_profit_objective_missing"] += 1
            if len(missing_samples) < 12:
                missing_samples.append({
                    "task_id": d.get("task_id"),
                    "task_type": task_type,
                    "stage": stage,
                    "goal_id": payload.get("goal_id"),
                    "payload_keys": sorted(payload.keys()),
                })

print("QUEUE_AUDIT=", dict(sorted(counts.items())))
print("PROFIT_OBJECTIVE_PRESENT_SAMPLES=", present_samples)
print("PROFIT_OBJECTIVE_MISSING_SAMPLES=", missing_samples)

queued = counts.get("queued_total", 0)
present = counts.get("queued_profit_objective_present", 0)
ratio = (present / queued) if queued else 0.0

print("QUEUED_OBJECTIVE_COVERAGE=", f"{present}/{queued}", f"({ratio:.1%})")

if explicit_files:
    print("HARD_CODED_PROFIT_DIRECTIVE=CONFIRMED")
else:
    print("HARD_CODED_PROFIT_DIRECTIVE=NOT_CONFIRMED")

if queued and ratio == 1.0:
    print("CURRENT_QUEUE_PROFIT_ALIGNMENT=FULL")
elif queued and ratio >= 0.90:
    print("CURRENT_QUEUE_PROFIT_ALIGNMENT=HIGH")
elif queued:
    print("CURRENT_QUEUE_PROFIT_ALIGNMENT=PARTIAL")
else:
    print("CURRENT_QUEUE_PROFIT_ALIGNMENT=NO_QUEUED_TASKS")

print("V65_72_PROFIT_OBJECTIVE_AUDIT=COMPLETE")
PY
