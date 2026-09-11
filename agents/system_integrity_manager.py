#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
AGENTS = ROOT / "agents"
CTL = ROOT / "companyos"
MEMORY = ROOT / "ceo_memory"
BACKUPS = ROOT / "backups"

CONFIG = MEMORY / "system_integrity_config.json"
REPORT = MEMORY / "system_integrity_report.json"
HEALTH = MEMORY / "system_integrity_health.json"
AUDIT = MEMORY / "system_integrity_audit.json"

CORE_COMMANDS = [
    "githubctl",
    "crmctl",
    "quotectl",
    "salesctl",
    "projectctl",
    "automationctl",
    "accountingctl",
    "executivectl",
    "opportunitydiscoveryctl",
    "priorityctl",
    "decisionctl",
    "executionplanctl",
    "improvementctl",
    "performancectl",
    "forecastctl",
]

CORE_MEMORY_FILES = [
    "executive_priority_config.json",
    "ceo_decision_config.json",
    "decision_execution_config.json",
    "continuous_improvement_config.json",
    "performance_analytics_config.json",
    "business_forecasting_config.json",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temp.replace(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit(action: str, result: dict[str, Any]) -> None:
    records = load_json(AUDIT, [])
    if not isinstance(records, list):
        records = []

    records.append({
        "timestamp": now(),
        "action": action,
        "success": result.get("success", False),
        "result": result,
    })

    save_json(AUDIT, records[-1000:])


def run_check() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {
            "success": False,
            "status": "system_integrity_manager_disabled",
        }
        audit("check", result)
        return result

    errors: list[str] = []
    warnings: list[str] = []
    files: list[dict[str, Any]] = []

    for directory in [AGENTS, CTL, MEMORY, BACKUPS]:
        if not directory.exists():
            errors.append(f"Missing directory: {directory}")
        elif not directory.is_dir():
            errors.append(f"Not a directory: {directory}")

    for command in CORE_COMMANDS:
        path = CTL / command

        if not path.exists():
            errors.append(f"Missing command: companyos/{command}")
            continue

        files.append({
            "path": str(path.relative_to(ROOT)),
            "size": path.stat().st_size,
            "sha256": sha256(path),
        })

        if path.stat().st_size <= 0:
            errors.append(f"Empty command file: companyos/{command}")

    json_files = sorted(MEMORY.glob("*.json"))

    if not json_files:
        errors.append("No memory JSON files found")

    for path in json_files:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"Invalid JSON: {path.name}: {exc}")

    for filename in CORE_MEMORY_FILES:
        path = MEMORY / filename
        if not path.exists():
            warnings.append(f"Missing optional safety config: {filename}")
            continue

        data = load_json(path, {})
        for field in [
            "automatic_task_execution",
            "automatic_external_execution",
            "automatic_publication",
            "automatic_spending",
        ]:
            if field in data and data[field] is not False:
                errors.append(
                    f"Safety failure: {filename}: {field} must be false"
                )

    report = {
        "generated_at": now(),
        "summary": {
            "errors": len(errors),
            "warnings": len(warnings),
            "checked_commands": len(CORE_COMMANDS),
            "checked_json_files": len(json_files),
        },
        "errors": errors,
        "warnings": warnings,
        "files": files,
        "automatic_repairs": False,
        "automatic_code_changes": False,
        "automatic_external_execution": False,
        "automatic_spending": False,
    }

    save_json(REPORT, report)
    save_json(
        HEALTH,
        {
            "healthy": len(errors) == 0,
            "last_checked_at": now(),
            "error_count": len(errors),
            "warning_count": len(warnings),
            "last_error": errors[0] if errors else None,
        },
    )

    result = {
        "success": len(errors) == 0,
        "status": (
            "system_integrity_check_passed"
            if not errors
            else "system_integrity_check_failed"
        ),
        "report": report,
    }
    audit("check", result)
    return result


def create_backup() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = BACKUPS / f"system_snapshot_{timestamp}"
    destination.mkdir(parents=True, exist_ok=False)

    copied = []

    for source in [AGENTS, CTL, MEMORY]:
        if not source.exists():
            continue

        target = destination / source.name
        shutil.copytree(source, target)
        copied.append(str(target.relative_to(ROOT)))

    manifest_files = []

    for path in destination.rglob("*"):
        if path.is_file():
            manifest_files.append({
                "path": str(path.relative_to(destination)),
                "size": path.stat().st_size,
                "sha256": sha256(path),
            })

    manifest = {
        "created_at": now(),
        "root": str(ROOT),
        "files": manifest_files,
        "automatic_repairs": False,
        "automatic_external_execution": False,
    }

    save_json(destination / "manifest.json", manifest)

    retention = int(config.get("backup_retention_count", 10))
    snapshots = sorted(
        [
            path for path in BACKUPS.glob("system_snapshot_*")
            if path.is_dir()
        ],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    removed = []

    for old in snapshots[retention:]:
        shutil.rmtree(old)
        removed.append(str(old))

    result = {
        "success": True,
        "status": "system_backup_created",
        "backup_path": str(destination),
        "copied": copied,
        "file_count": len(manifest_files),
        "removed_old_backups": removed,
        "automatic_repairs": False,
        "automatic_external_execution": False,
    }

    audit("backup", result)
    return result


def list_backups() -> dict[str, Any]:
    backups = []

    for path in sorted(
        BACKUPS.glob("system_snapshot_*"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    ):
        manifest = load_json(path / "manifest.json", {})
        backups.append({
            "name": path.name,
            "path": str(path),
            "created_at": manifest.get("created_at"),
            "file_count": len(manifest.get("files", [])),
        })

    result = {
        "success": True,
        "status": "system_backup_list",
        "count": len(backups),
        "backups": backups,
    }
    audit("list_backups", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    health = load_json(HEALTH, {})

    result = {
        "success": True,
        "status": "system_integrity_manager_status",
        "enabled": config.get("enabled", False),
        "automatic_internal_integrity_checks": config.get(
            "automatic_internal_integrity_checks", False
        ),
        "automatic_local_backups": config.get(
            "automatic_local_backups", False
        ),
        "automatic_repairs": config.get("automatic_repairs", False),
        "automatic_code_changes": config.get(
            "automatic_code_changes", False
        ),
        "automatic_task_execution": config.get(
            "automatic_task_execution", False
        ),
        "automatic_external_execution": config.get(
            "automatic_external_execution", False
        ),
        "automatic_publication": config.get(
            "automatic_publication", False
        ),
        "automatic_spending": config.get(
            "automatic_spending", False
        ),
        "health": health,
    }
    audit("status", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    try:
        if action == "check":
            return print_result(run_check())

        if action == "backup":
            return print_result(create_backup())

        if action == "list-backups":
            return print_result(list_backups())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_integrity_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "system_integrity_error",
            "error": str(exc),
        }

        save_json(
            HEALTH,
            {
                "healthy": False,
                "last_checked_at": now(),
                "last_error": str(exc),
            },
        )

        audit("error", result)
        print(json.dumps(result, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
