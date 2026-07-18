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

CFG = MEM / "github_change_config.json"
STATE = MEM / "github_change_state.json"
REPORT = MEM / "github_change_report.json"
HEALTH = MEM / "github_change_health.json"

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

def git(*args: str) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60
        )
        return {
            "success": proc.returncode == 0,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip()
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}

def analyze() -> dict[str, Any]:
    cfg = load(CFG, {})
    if not cfg.get("enabled", True):
        return {"success": False, "status": "github_change_intelligence_disabled"}

    status = git("status", "--porcelain")
    diffstat = git("diff", "--stat")
    changed = git("diff", "--name-only")
    staged = git("diff", "--cached", "--name-only")

    unstaged_files = [
        x for x in changed.get("stdout", "").splitlines() if x.strip()
    ]
    staged_files = [
        x for x in staged.get("stdout", "").splitlines() if x.strip()
    ]
    all_files = sorted(set(unstaged_files + staged_files))

    high_patterns = cfg.get("high_risk_file_patterns", [])
    high_risk_files = [
        f for f in all_files
        if any(pattern in f for pattern in high_patterns)
    ]

    risk = 0
    reasons = []

    if all_files:
        risk += min(30, len(all_files) * 3)
        reasons.append(f"{len(all_files)} changed file(s) detected")

    if high_risk_files:
        risk += min(50, len(high_risk_files) * 15)
        reasons.append("High-risk control files changed")

    if staged_files and unstaged_files:
        risk += 10
        reasons.append("Both staged and unstaged changes exist")

    risk = min(100, risk)

    if risk >= 70:
        band = "high"
    elif risk >= 35:
        band = "medium"
    else:
        band = "low"

    recommendations = []
    if not all_files:
        recommendations.append("No local code changes detected.")
    else:
        recommendations.append("Run tests before push.")
        if high_risk_files:
            recommendations.append("Review high-risk control files before deployment.")
        if band == "high":
            recommendations.append("Require explicit owner review before production deployment.")

    report = {
        "generated_at": now(),
        "risk_score": risk,
        "risk_band": band,
        "reasons": reasons,
        "changed_files": all_files,
        "high_risk_files": high_risk_files,
        "diff_stat": diffstat.get("stdout"),
        "working_tree_status": status.get("stdout"),
        "recommendations": recommendations,
        "automatic_repository_mutation": False,
        "automatic_issue_creation": False,
        "automatic_pull_request_creation": False,
        "automatic_merge": False
    }

    save(REPORT, report)
    save(STATE, {
        "generated_at": now(),
        "risk_score": risk,
        "risk_band": band,
        "changed_file_count": len(all_files),
        "high_risk_file_count": len(high_risk_files)
    })
    save(HEALTH, {
        "healthy": True,
        "last_analyzed_at": now(),
        "risk_score": risk,
        "risk_band": band
    })

    return {
        "success": True,
        "status": "github_change_intelligence_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "github_change_intelligence_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "analyze":
        result = analyze()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["analyze", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
