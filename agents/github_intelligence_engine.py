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

CFG = MEM / "github_intelligence_config.json"
STATE = MEM / "github_intelligence_state.json"
REPORT = MEM / "github_intelligence_report.json"
HEALTH = MEM / "github_intelligence_health.json"
CACHE = MEM / "github_read_cache.json"
GIT_STATUS = MEM / "github_connector_audit.json"

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

def run_git(*args: str) -> dict[str, Any]:
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
        result = {"success": False, "status": "github_intelligence_disabled"}
        print(json.dumps(result, indent=2))
        return result

    repos = load(CACHE, {}).get("repositories", [])
    repo = next(
        (r for r in repos if r.get("full_name") == cfg.get("repository")),
        None
    )

    branch = run_git("branch", "--show-current")
    status = run_git("status", "--porcelain")
    latest = run_git("log", "-1", "--pretty=%H|%cI|%s")

    working_tree_clean = bool(status.get("success")) and not status.get("stdout")
    branch_name = branch.get("stdout") if branch.get("success") else None

    commit_hash = None
    commit_time = None
    commit_subject = None
    if latest.get("success") and latest.get("stdout"):
        parts = latest["stdout"].split("|", 2)
        if len(parts) == 3:
            commit_hash, commit_time, commit_subject = parts

    signals = []
    recommendations = []

    if branch_name != "main":
        signals.append("not_on_main_branch")
        recommendations.append("Review the active Git branch before production changes.")

    if not working_tree_clean:
        signals.append("uncommitted_changes")
        recommendations.append("Review and either commit or restore uncommitted changes.")

    if repo is None:
        signals.append("repository_cache_missing")
        recommendations.append("Refresh the GitHub read connector repository cache.")
    else:
        if repo.get("default_branch") != "main":
            signals.append("default_branch_not_main")

    if not signals:
        signals.append("repository_operating_normally")
        recommendations.append("Repository state looks healthy; continue normal autonomous monitoring.")

    report = {
        "generated_at": now(),
        "repository": cfg.get("repository"),
        "live_repository_data": repo,
        "local_git": {
            "branch": branch_name,
            "working_tree_clean": working_tree_clean,
            "latest_commit_hash": commit_hash,
            "latest_commit_time": commit_time,
            "latest_commit_subject": commit_subject
        },
        "signals": signals,
        "recommendations": recommendations,
        "automatic_repository_mutation": False,
        "automatic_issue_creation": False,
        "automatic_pull_request_creation": False
    }

    save(REPORT, report)
    save(STATE, {
        "generated_at": now(),
        "signal_count": len(signals),
        "working_tree_clean": working_tree_clean,
        "branch": branch_name
    })
    save(HEALTH, {
        "healthy": True,
        "last_analyzed_at": now(),
        "signal_count": len(signals),
        "working_tree_clean": working_tree_clean
    })

    return {
        "success": True,
        "status": "github_intelligence_analysis_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "github_intelligence_status",
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
