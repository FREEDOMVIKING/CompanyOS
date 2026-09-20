#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"

python - <<'PY'
import json, re, subprocess, time
from pathlib import Path

ROOT = Path.home() / "companyos"
RT = ROOT / ".companyos_runtime"

def read_json(p):
    try:
        x = json.loads(p.read_text(encoding="utf-8"))
        return x if isinstance(x, dict) else {}
    except Exception:
        return {}

def newest(paths):
    paths = [p for p in paths if p.exists()]
    if not paths:
        return None, {}
    p = max(paths, key=lambda x: x.stat().st_mtime)
    return p, read_json(p)

sup = read_json(RT / "service_supervisor_state.json")
wd = read_json(RT / "productive_autonomy_watchdog_state.json")
runtime_path, runtime = newest([
    RT / "autonomous_ceo_runtime_service.json",
    ROOT / "companyos_runtime" / "autonomous_ceo_runtime_service.json",
])

cycles = int(runtime.get("cycle_count", 0) or 0)
baseline = int(wd.get("last_cycle_count", 0) or 0)
delta = cycles - baseline

if delta < 0:
    delta_class = "counter_reset_or_state_generation_mismatch"
    delta_note = (
        "Current CEO cycle counter is lower than the watchdog baseline. "
        "This usually happens after a runtime restart/recovery while the "
        "watchdog retains its prior baseline; by itself it is not a failure."
    )
else:
    delta_class = "normal"
    delta_note = ""

services = {}
for name, info in (sup.get("services") or {}).items():
    info = info or {}
    services[name] = {
        "pid": info.get("pid"),
        "running": bool(info.get("running")),
        "restarts": int(info.get("restarts", 0) or 0),
        "consecutive_failures": int(info.get("consecutive_failures", 0) or 0),
        "returncode": info.get("returncode"),
    }

cand = RT / "profit_first_candidates"
candidate_files = []
if cand.exists():
    candidate_files = sorted(
        [p for p in cand.rglob("*.json") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

log_paths = [
    RT / "productive_autonomy_watchdog.log",
    RT / "service_supervisor.log",
    RT / "runtime_control.log",
]
patterns = {
    "failures": re.compile(r"ERROR|FATAL|Traceback|failed", re.I),
    "deployments": re.compile(r"deploy|deployment|published|live_url", re.I),
    "outreach": re.compile(r"smtp|email|outreach|sent", re.I),
    "revenue": re.compile(r"revenue|customer|sale|invoice|payment", re.I),
    "research": re.compile(r"PROFIT_FIRST_RESEARCH|CANDIDATES_MATERIALIZED"),
}
hits = {k: [] for k in patterns}

for lp in log_paths:
    if not lp.exists():
        continue
    lines = lp.read_text(encoding="utf-8", errors="replace").splitlines()[-4000:]
    for line in lines:
        for key, pat in patterns.items():
            if pat.search(line):
                hits[key].append({"log": lp.name, "line": line[-900:]})

for k in hits:
    hits[k] = hits[k][-30:]

active = int(runtime.get("active_orchestrations", 0) or 0)
completed = int(runtime.get("completed_orchestrations", 0) or 0)
failed = int(runtime.get("failed_orchestrations", 0) or 0)
halted = int(runtime.get("halted_orchestrations", 0) or 0)

assessment = []
if services and all(x["running"] for x in services.values()):
    assessment.append("all_supervised_services_running")
if failed == 0 and halted == 0:
    assessment.append("no_failed_or_halted_orchestrations")
if completed:
    assessment.append("completed_work_present")
if active:
    assessment.append("active_work_present")
if candidate_files or hits["research"]:
    assessment.append("research_candidate_generation_active")
if hits["deployments"]:
    assessment.append("deployment_activity_detected")
if hits["outreach"]:
    assessment.append("outreach_activity_detected")
if hits["revenue"]:
    assessment.append("revenue_customer_activity_detected")

report = {
    "generated_at_unix": time.time(),
    "runtime_state_path": str(runtime_path) if runtime_path else None,
    "runtime": {
        "running": runtime.get("running"),
        "ready": runtime.get("ready"),
        "cycle_count": cycles,
        "active_orchestrations": active,
        "completed_orchestrations": completed,
        "failed_orchestrations": failed,
        "halted_orchestrations": halted,
    },
    "watchdog": {
        "total_autostarts": int(wd.get("total_autostarts", 0) or 0),
        "last_cycle_count": baseline,
        "last_completed": wd.get("last_completed"),
        "last_seen": wd.get("last_seen"),
    },
    "delta_investigation": {
        "delta_cycles": delta,
        "classification": delta_class,
        "note": delta_note,
    },
    "services": services,
    "candidate_json_count": len(candidate_files),
    "recent_candidate_files": [
        str(p.relative_to(ROOT)) for p in candidate_files[:15]
    ],
    "activity_hits": hits,
    "assessment": assessment,
}

out = RT / f"investigation_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

print("===== COMPANYOS INVESTIGATION =====")
print("runtime_state:", report["runtime_state_path"])
print("runtime:", report["runtime"])
print("services:", report["services"])
print("watchdog_total_autostarts:", report["watchdog"]["total_autostarts"])
print("delta_cycles:", delta)
print("delta_classification:", delta_class)
print("candidate_json_count:", len(candidate_files))
print("failure_hits:", len(hits["failures"]))
print("deployment_hits:", len(hits["deployments"]))
print("outreach_hits:", len(hits["outreach"]))
print("revenue_hits:", len(hits["revenue"]))
print("assessment:", ", ".join(assessment))
print("report_file:", out)

print("\n===== RECENT FAILURES =====")
for x in hits["failures"][-12:]:
    print(f"{x['log']}: {x['line']}")

print("\n===== RECENT DEPLOY / OUTREACH / REVENUE =====")
for key in ("deployments", "outreach", "revenue"):
    print("---", key, "---")
    for x in hits[key][-10:]:
        print(f"{x['log']}: {x['line']}")

print("\n===== RECENT CANDIDATES =====")
for p in report["recent_candidate_files"]:
    print(p)
PY
