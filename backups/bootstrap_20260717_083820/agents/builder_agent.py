#!/usr/bin/env python3

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
BUILD_DIR = BASE_DIR / "company_builds"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip().lower())
    return cleaned.strip("_") or "unnamed_project"


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_prototype(task: dict[str, Any]) -> dict[str, Any]:
    payload = task.get("payload", {})

    project_name = payload.get("project_name", "Unnamed Project")
    problem = payload.get("problem", "Problem not defined")
    target_customer = payload.get(
        "target_customer",
        "Target customer not defined",
    )
    solution = payload.get(
        "solution",
        "A simple digital tool that addresses the stated problem",
    )

    project_slug = safe_name(project_name)
    project_dir = BUILD_DIR / project_slug

    if project_dir.exists():
        return {
            "success": False,
            "error": f"Project already exists: {project_dir}",
        }

    project_dir.mkdir(parents=True, exist_ok=False)

    readme = f"""# {project_name}

## Problem
{problem}

## Target customer
{target_customer}

## Proposed solution
{solution}

## Current stage
Prototype

## Next validation steps
1. Confirm the customer problem.
2. Show the prototype to potential users.
3. Record feedback.
4. Improve only if demand is demonstrated.
"""

    app_code = f'''#!/usr/bin/env python3

PROJECT_NAME = {project_name!r}
PROBLEM = {problem!r}
TARGET_CUSTOMER = {target_customer!r}
SOLUTION = {solution!r}


def get_project_summary() -> dict:
    return {{
        "project_name": PROJECT_NAME,
        "problem": PROBLEM,
        "target_customer": TARGET_CUSTOMER,
        "solution": SOLUTION,
        "status": "prototype",
    }}


if __name__ == "__main__":
    print(get_project_summary())
'''

    test_code = '''#!/usr/bin/env python3

from app import get_project_summary


def test_project_summary():
    result = get_project_summary()

    assert isinstance(result, dict)
    assert result["project_name"]
    assert result["problem"]
    assert result["target_customer"]
    assert result["solution"]
    assert result["status"] == "prototype"


if __name__ == "__main__":
    test_project_summary()
    print("PROTOTYPE_TEST_PASSED")
'''

    manifest = {
        "project_name": project_name,
        "project_slug": project_slug,
        "problem": problem,
        "target_customer": target_customer,
        "solution": solution,
        "stage": "prototype",
        "created_by": "builder_agent",
        "created_at": now(),
    }

    write_file(project_dir / "README.md", readme)
    write_file(project_dir / "app.py", app_code)
    write_file(project_dir / "test_app.py", test_code)
    write_file(
        project_dir / "manifest.json",
        json.dumps(manifest, indent=2),
    )

    return {
        "success": True,
        "status": "prototype_created",
        "project_directory": str(project_dir),
        "files_created": [
            "README.md",
            "app.py",
            "test_app.py",
            "manifest.json",
        ],
        "manifest": manifest,
    }


def run_task(task: dict[str, Any]) -> dict[str, Any]:
    action = task.get("action")

    if action != "build_prototype":
        return {
            "success": False,
            "error": f"Unsupported builder action: {action}",
        }

    return build_prototype(task)


if __name__ == "__main__":
    sample_task = {
        "id": "sample-builder-task",
        "action": "build_prototype",
        "payload": {
            "project_name": "Digital Template Business",
            "problem": "Small businesses need ready-made documents",
            "target_customer": "Small business owners",
            "solution": "A searchable library of editable business templates",
        },
    }

    print(json.dumps(run_task(sample_task), indent=2))
