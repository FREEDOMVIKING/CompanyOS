#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"
CONFIG_PATH = MEMORY / "github_connector.json"
AUDIT_PATH = MEMORY / "github_connector_audit.json"
APPROVAL_PATH = MEMORY / "github_push_approval.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=False),
        encoding="utf-8",
    )
    temporary.replace(path)


def run_git(*arguments: str, check: bool = False) -> dict[str, Any]:
    command = ["git", "-C", str(ROOT), *arguments]

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=120,
    )

    result = {
        "success": completed.returncode == 0,
        "returncode": completed.returncode,
        "command": command,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }

    if check and completed.returncode != 0:
        raise RuntimeError(
            completed.stderr.strip()
            or completed.stdout.strip()
            or "Git command failed"
        )

    return result


def audit(action: str, result: dict[str, Any]) -> None:
    records = load_json(AUDIT_PATH, [])

    records.append(
        {
            "timestamp": now(),
            "action": action,
            "success": result.get("success", False),
            "result": result,
        }
    )

    save_json(AUDIT_PATH, records[-500:])


def get_config() -> dict[str, Any]:
    config = load_json(CONFIG_PATH, {})

    if not config:
        raise RuntimeError("GitHub connector configuration is missing")

    return config


def repository_health() -> dict[str, Any]:
    config = get_config()

    inside = run_git("rev-parse", "--is-inside-work-tree")
    branch = run_git("branch", "--show-current")
    remote = run_git("remote", "get-url", "origin")
    status = run_git("status", "--porcelain")

    healthy = (
        inside["success"]
        and inside["stdout"] == "true"
        and branch["success"]
        and remote["success"]
    )

    config["health"] = "healthy" if healthy else "unhealthy"
    config["last_checked_at"] = now()
    config["last_error"] = None if healthy else (
        remote["stderr"]
        or branch["stderr"]
        or inside["stderr"]
        or "Repository health check failed"
    )

    save_json(CONFIG_PATH, config)

    result = {
        "success": healthy,
        "status": "github_connector_health",
        "repository": config.get("repository"),
        "local_path": str(ROOT),
        "branch": branch["stdout"],
        "remote": remote["stdout"],
        "working_tree_changes": len(
            [line for line in status["stdout"].splitlines() if line.strip()]
        ),
        "automatic_commit": config.get("automatic_commit", False),
        "automatic_push": config.get("automatic_push", False),
        "owner_approval_required": config.get(
            "require_owner_approval_for_push",
            True,
        ),
        "health": config["health"],
        "last_error": config["last_error"],
    }

    audit("health", result)
    return result


def status() -> dict[str, Any]:
    branch = run_git("branch", "--show-current")
    porcelain = run_git("status", "--porcelain")
    ahead_behind = run_git(
        "rev-list",
        "--left-right",
        "--count",
        "origin/main...HEAD",
    )

    staged = 0
    modified = 0
    untracked = 0

    for line in porcelain["stdout"].splitlines():
        if line.startswith("??"):
            untracked += 1
            continue

        if len(line) >= 2:
            if line[0] != " ":
                staged += 1
            if line[1] != " ":
                modified += 1

    ahead = None
    behind = None

    if ahead_behind["success"] and ahead_behind["stdout"]:
        parts = ahead_behind["stdout"].split()
        if len(parts) == 2:
            behind = int(parts[0])
            ahead = int(parts[1])

    result = {
        "success": branch["success"] and porcelain["success"],
        "status": "github_repository_status",
        "branch": branch["stdout"],
        "staged_files": staged,
        "modified_files": modified,
        "untracked_files": untracked,
        "ahead_of_remote": ahead,
        "behind_remote": behind,
        "clean": not bool(porcelain["stdout"]),
    }

    audit("status", result)
    return result


def diff() -> dict[str, Any]:
    unstaged = run_git("diff", "--stat")
    staged = run_git("diff", "--cached", "--stat")

    result = {
        "success": unstaged["success"] and staged["success"],
        "status": "github_repository_diff",
        "unstaged": unstaged["stdout"],
        "staged": staged["stdout"],
    }

    audit("diff", result)
    return result


def history(limit: int = 10) -> dict[str, Any]:
    log = run_git(
        "log",
        f"-{max(1, min(limit, 100))}",
        "--pretty=format:%h | %ad | %an | %s",
        "--date=iso",
    )

    result = {
        "success": log["success"],
        "status": "github_repository_history",
        "history": log["stdout"].splitlines() if log["stdout"] else [],
        "error": log["stderr"] or None,
    }

    audit("history", result)
    return result


def stage() -> dict[str, Any]:
    gitignore = ROOT / ".gitignore"

    if not gitignore.exists():
        gitignore.write_text(
            "\n".join(
                [
                    "# Python",
                    "__pycache__/",
                    "*.py[cod]",
                    "",
                    "# Runtime state",
                    "*.pid",
                    "*.log",
                    "",
                    "# CompanyOS secrets",
                    ".env",
                    "*.env",
                    "secrets/",
                    "",
                    "# Local backups",
                    "backups/",
                    "",
                    "# Editor files",
                    ".idea/",
                    ".vscode/",
                    "*.swp",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    operation = run_git("add", "--all")

    result = {
        "success": operation["success"],
        "status": "github_files_staged",
        "error": operation["stderr"] or None,
    }

    audit("stage", result)
    return result


def commit(message: str) -> dict[str, Any]:
    if not message.strip():
        raise ValueError("Commit message cannot be empty")

    operation = run_git("commit", "-m", message.strip())

    no_changes = "nothing to commit" in (
        operation["stdout"] + operation["stderr"]
    ).lower()

    result = {
        "success": operation["success"] or no_changes,
        "status": (
            "github_commit_created"
            if operation["success"]
            else "github_nothing_to_commit"
        ),
        "message": message.strip(),
        "output": operation["stdout"],
        "error": None if no_changes else operation["stderr"] or None,
    }

    audit("commit", result)
    return result


def create_push_approval() -> dict[str, Any]:
    approval = {
        "approved": True,
        "approved_at": now(),
        "expires_after_one_use": True,
        "repository": "FREEDOMVIKING/CompanyOS",
    }

    save_json(APPROVAL_PATH, approval)

    result = {
        "success": True,
        "status": "github_push_approved",
        "approval": approval,
    }

    audit("approve_push", result)
    return result


def consume_push_approval() -> bool:
    approval = load_json(APPROVAL_PATH, {})

    if not approval.get("approved"):
        return False

    approval["approved"] = False
    approval["consumed_at"] = now()
    save_json(APPROVAL_PATH, approval)
    return True


def push() -> dict[str, Any]:
    config = get_config()

    approval_required = config.get(
        "require_owner_approval_for_push",
        True,
    )

    if approval_required and not consume_push_approval():
        result = {
            "success": False,
            "status": "github_push_blocked",
            "reason": "Owner approval is required",
            "next_command": "python companyos/githubctl approve-push",
        }
        audit("push_blocked", result)
        return result

    operation = run_git("push", "origin", "main")

    result = {
        "success": operation["success"],
        "status": (
            "github_push_complete"
            if operation["success"]
            else "github_push_failed"
        ),
        "output": operation["stdout"],
        "error": operation["stderr"] or None,
    }

    audit("push", result)
    return result


def pull() -> dict[str, Any]:
    operation = run_git("pull", "--ff-only", "origin", "main")

    result = {
        "success": operation["success"],
        "status": (
            "github_pull_complete"
            if operation["success"]
            else "github_pull_failed"
        ),
        "output": operation["stdout"],
        "error": operation["stderr"] or None,
    }

    audit("pull", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "Usage: github_connector.py "
            "health|status|diff|history|stage|commit|pull|"
            "approve-push|push"
        )
        return 2

    action = sys.argv[1].lower()

    try:
        if action == "health":
            return print_result(repository_health())

        if action == "status":
            return print_result(status())

        if action == "diff":
            return print_result(diff())

        if action == "history":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            return print_result(history(limit))

        if action == "stage":
            return print_result(stage())

        if action == "commit":
            message = " ".join(sys.argv[2:]).strip()
            return print_result(commit(message))

        if action == "pull":
            return print_result(pull())

        if action == "approve-push":
            return print_result(create_push_approval())

        if action == "push":
            return print_result(push())

        print(json.dumps({
            "success": False,
            "error": f"Unknown action: {action}",
        }, indent=2))
        return 2

    except Exception as exc:
        result = {
            "success": False,
            "status": "github_connector_error",
            "action": action,
            "error": str(exc),
        }
        audit("error", result)
        print(json.dumps(result, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
