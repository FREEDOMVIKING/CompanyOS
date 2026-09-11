#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"
RELEASES = ROOT / "releases"

CONFIG = MEMORY / "release_readiness_config.json"
EVALUATIONS = MEMORY / "prototype_evaluations.json"
PROTOTYPES = MEMORY / "prototype_registry.json"
REGISTRY = MEMORY / "release_registry.json"
HEALTH = MEMORY / "release_readiness_health.json"
AUDIT = MEMORY / "release_readiness_audit.json"


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


def latest_evaluation() -> dict[str, Any]:
    records = load_json(EVALUATIONS, {}).get("evaluations", [])
    if not records:
        raise RuntimeError("No prototype evaluation found")
    return records[-1]


def latest_prototype() -> dict[str, Any]:
    records = load_json(PROTOTYPES, {}).get("prototypes", [])
    if not records:
        raise RuntimeError("No prototype found")
    return records[-1]


def safe_name(value: str) -> str:
    text = "".join(c.lower() if c.isalnum() else "_" for c in value)
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("_") or "release"


def validate_release() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    evaluation = latest_evaluation()
    prototype = latest_prototype()

    score = int(evaluation.get("score", 0))
    decision = str(evaluation.get("decision", "failed"))
    minimum = int(config.get("minimum_release_score", 88))

    current = Path(
        str(
            prototype.get("current_directory")
            or prototype.get("directory")
            or ""
        )
    )

    required = [
        current / "frontend" / "index.html",
        current / "frontend" / "styles.css",
        current / "frontend" / "app.js",
        current / "server.py",
        current / "README.md",
    ]

    missing = [str(path) for path in required if not path.exists()]

    release_ready = (
        score >= minimum
        and decision == "release_ready"
        and not missing
    )

    checklist = {
        "prototype_exists": current.exists(),
        "required_files_present": not missing,
        "evaluation_score_passed": score >= minimum,
        "evaluation_decision_release_ready": decision == "release_ready",
        "owner_approval_required": True,
        "external_deployment_authorized": False,
        "external_publication_authorized": False,
        "automatic_spending_authorized": False,
    }

    result = {
        "success": True,
        "status": "release_readiness_complete",
        "project_name": prototype.get("project_name"),
        "prototype_id": prototype.get("id"),
        "prototype_version": prototype.get("version"),
        "evaluation_score": score,
        "evaluation_decision": decision,
        "minimum_release_score": minimum,
        "release_ready": release_ready,
        "missing_files": missing,
        "checklist": checklist,
        "owner_approval_required": True,
        "automatic_external_deployment": False,
        "automatic_publication": False,
        "automatic_spending": False,
    }

    audit("validate", result)
    return result


def package_release() -> dict[str, Any]:
    readiness = validate_release()

    if not readiness.get("release_ready"):
        result = {
            "success": False,
            "status": "release_packaging_blocked",
            "reason": "Prototype is not release ready",
            "readiness": readiness,
        }
        audit("package", result)
        return result

    prototype = latest_prototype()
    source = Path(
        str(
            prototype.get("current_directory")
            or prototype.get("directory")
        )
    )

    project_name = str(prototype.get("project_name") or "project")
    version = int(prototype.get("version", 1))
    release_id = f"{safe_name(project_name)}-v{version}"

    release_dir = RELEASES / release_id
    bundle = RELEASES / f"{release_id}.tar.gz"

    if release_dir.exists():
        shutil.rmtree(release_dir)

    shutil.copytree(source, release_dir)

    report = {
        "release_id": release_id,
        "project_name": project_name,
        "prototype_id": prototype.get("id"),
        "prototype_version": version,
        "status": "packaged",
        "owner_release_approval_required": True,
        "external_deployment_authorized": False,
        "external_publication_authorized": False,
        "automatic_spending_authorized": False,
        "created_at": now(),
    }

    (release_dir / "RELEASE_REPORT.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    with tarfile.open(bundle, "w:gz") as archive:
        archive.add(release_dir, arcname=release_id)

    registry = load_json(
        REGISTRY,
        {
            "schema_version": 1,
            "releases": [],
            "statistics": {},
        },
    )

    records = registry.setdefault("releases", [])
    records[:] = [
        item for item in records
        if item.get("release_id") != release_id
    ]

    record = {
        **report,
        "directory": str(release_dir),
        "bundle": str(bundle),
        "bundle_exists": bundle.exists(),
        "bundle_size_bytes": bundle.stat().st_size if bundle.exists() else 0,
    }

    records.append(record)

    registry["statistics"] = {
        "total": len(records),
        "ready": sum(
            1 for item in records
            if item.get("status") in {"ready", "packaged"}
        ),
        "blocked": sum(
            1 for item in records
            if item.get("status") == "blocked"
        ),
        "packaged": sum(
            1 for item in records
            if item.get("status") == "packaged"
        ),
    }
    registry["last_updated_at"] = now()
    save_json(REGISTRY, registry)

    save_json(
        HEALTH,
        {
            "healthy": True,
            "latest_release_id": release_id,
            "latest_bundle": str(bundle),
            "last_error": None,
            "updated_at": now(),
        },
    )

    result = {
        "success": True,
        "status": "release_package_created",
        "release_id": release_id,
        "directory": str(release_dir),
        "bundle": str(bundle),
        "bundle_size_bytes": record["bundle_size_bytes"],
        "owner_release_approval_required": True,
        "automatic_external_deployment": False,
        "automatic_publication": False,
        "automatic_spending": False,
    }

    audit("package", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    registry = load_json(REGISTRY, {})
    health = load_json(HEALTH, {})

    result = {
        "success": True,
        "status": "release_readiness_status",
        "enabled": config.get("enabled", False),
        "automatic_packaging": config.get("automatic_packaging", False),
        "automatic_release_approval": config.get(
            "automatic_release_approval", False
        ),
        "automatic_external_deployment": config.get(
            "automatic_external_deployment", False
        ),
        "automatic_publication": config.get("automatic_publication", False),
        "automatic_spending": config.get("automatic_spending", False),
        "owner_approval_required": config.get("owner_approval_required", True),
        "statistics": registry.get("statistics", {}),
        "health": health,
    }

    audit("status", result)
    return result


def latest() -> dict[str, Any]:
    records = load_json(REGISTRY, {}).get("releases", [])

    result = {
        "success": bool(records),
        "status": "latest_release",
        "release": records[-1] if records else None,
    }

    audit("latest", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    try:
        if action == "validate":
            return print_result(validate_release())

        if action == "package":
            return print_result(package_release())

        if action == "status":
            return print_result(status())

        if action == "latest":
            return print_result(latest())

        return print_result({
            "success": False,
            "status": "unknown_release_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "release_readiness_error",
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
