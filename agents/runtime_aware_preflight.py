#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "preflight2_config.json"
STATE = MEM / "preflight2_state.json"
REPORT = MEM / "preflight2_report.json"
HEALTH = MEM / "preflight2_health.json"

HYGIENE = MEM / "runtime_hygiene_state.json"
GH_HEALTH = MEM / "github_read_health.json"
RISK = MEM / "github_change_report.json"

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save(path: Path, data: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)

def run_hygiene() -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["python", "companyos/runtimehygienectl", "isolate"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=180
        )
        return {
            "success": proc.returncode == 0,
            "stdout": proc.stdout[-2500:],
            "stderr": proc.stderr[-1200:]
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}

def evaluate() -> dict[str, Any]:
    cfg = load(CFG, {})
    hygiene_run = None

    if cfg.get("require_runtime_hygiene_check", True):
        hygiene_run = run_hygiene()

    hygiene = load(HYGIENE, {})
    github = load(GH_HEALTH, {})
    risk = load(RISK, {})

    blockers = []
    warnings = []

    source_changes = int(hygiene.get("source_change_count", 0))
    runtime_changes = int(hygiene.get("runtime_only_change_count", 0))
    effectively_clean = bool(hygiene.get("working_tree_effectively_clean", False))
    risk_score = int(risk.get("risk_score", 0))

    if cfg.get("require_no_source_changes_for_ready_state", True) and not effectively_clean:
        blockers.append("source_controlled_changes_present")

    if cfg.get("require_github_connector_health", True) and github.get("healthy") is False:
        blockers.append("github_connector_unhealthy")

    if risk_score > int(cfg.get("maximum_change_risk_score", 34)):
        blockers.append("change_risk_above_threshold")

    if runtime_changes and cfg.get("allow_runtime_only_changes", True):
        warnings.append(f"{runtime_changes} runtime-only change(s) ignored for readiness")

    decision = "ready" if not blockers else "blocked"

    report = {
        "generated_at": now(),
        "decision": decision,
        "blockers": blockers,
        "warnings": warnings,
        "runtime_hygiene_run": hygiene_run,
        "source_change_count": source_changes,
        "runtime_only_change_count": runtime_changes,
        "working_tree_effectively_clean": effectively_clean,
        "github_connector_healthy": github.get("healthy"),
        "change_risk_score": risk_score,
        "automatic_git_reset": False,
        "automatic_git_clean": False,
        "automatic_commit": False,
        "automatic_push": False,
        "automatic_deploy": False
    }

    save(REPORT, report)
    save(STATE, {
        "last_evaluated_at": now(),
        "decision": decision,
        "blocker_count": len(blockers),
        "warning_count": len(warnings)
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "decision": decision,
        "blocker_count": len(blockers)
    })

    return {
        "success": True,
        "status": "runtime_aware_preflight_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "runtime_aware_preflight_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "run":
        result = evaluate()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["run", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
