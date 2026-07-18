#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEMORY="$ROOT/ceo_memory"
RELEASES="$ROOT/releases"
BACKUP="$ROOT/backups/phase15_step9_repair_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEMORY" "$RELEASES" "$BACKUP"

echo "============================================================"
echo " Phase 15 Step 9 Repair - Release Approval and Activation"
echo "============================================================"

for file in \
  "$AGENTS/release_approval_manager.py" \
  "$CTL/releaseapprovalctl" \
  "$MEMORY/release_approval_config.json" \
  "$MEMORY/release_approval_audit.json" \
  "$MEMORY/release_activation_state.json" \
  "$MEMORY/release_approval_health.json" \
  "$MEMORY/release_registry.json"
do
  if [ -f "$file" ]; then
    cp -a "$file" "$BACKUP/"
  fi
done

cat > "$MEMORY/release_approval_config.json" <<'JSON'
{
  "enabled": true,
  "owner_approval_required": true,
  "automatic_release_approval": false,
  "automatic_local_activation": false,
  "automatic_external_deployment": false,
  "automatic_publication": false,
  "automatic_spending": false
}
JSON

[ -f "$MEMORY/release_approval_audit.json" ] || echo '[]' > "$MEMORY/release_approval_audit.json"

cat > "$MEMORY/release_activation_state.json" <<'JSON'
{
  "active_release_id": null,
  "active_directory": null,
  "activated_at": null,
  "status": "inactive"
}
JSON

echo "[1/7] Ensuring a packaged release exists..."

python - <<'PY'
from __future__ import annotations

import json
import shutil
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

root = Path.home() / "companyos"
memory = root / "ceo_memory"
releases_dir = root / "releases"

registry_path = memory / "release_registry.json"
prototype_path = memory / "prototype_registry.json"

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)

registry = load_json(
    registry_path,
    {
        "schema_version": 1,
        "releases": [],
        "statistics": {},
        "last_updated_at": None,
    },
)

releases = registry.setdefault("releases", [])

usable = [
    item for item in releases
    if item.get("status") in {"packaged", "approved", "active"}
    and Path(str(item.get("directory", ""))).exists()
]

if not usable:
    prototypes = load_json(prototype_path, {}).get("prototypes", [])
    if not prototypes:
        raise SystemExit("ERROR: No prototype available to package.")

    prototype = prototypes[-1]
    source = Path(
        str(
            prototype.get("current_directory")
            or prototype.get("directory")
            or ""
        )
    )

    if not source.exists():
        raise SystemExit(f"ERROR: Prototype directory missing: {source}")

    project_name = str(prototype.get("project_name") or "companyos_product")
    version = int(prototype.get("version", 1))

    safe = "".join(
        c.lower() if c.isalnum() else "_"
        for c in project_name
    ).strip("_") or "release"

    release_id = f"{safe}-v{version}"
    release_dir = releases_dir / release_id
    bundle = releases_dir / f"{release_id}.tar.gz"

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

    releases[:] = [
        item for item in releases
        if item.get("release_id") != release_id
    ]

    releases.append({
        **report,
        "directory": str(release_dir),
        "bundle": str(bundle),
        "bundle_exists": bundle.exists(),
        "bundle_size_bytes": bundle.stat().st_size if bundle.exists() else 0,
    })

registry["statistics"] = {
    "total": len(releases),
    "ready": sum(
        1 for item in releases
        if item.get("status") in {"packaged", "approved", "active"}
    ),
    "blocked": sum(
        1 for item in releases
        if item.get("status") == "blocked"
    ),
    "packaged": sum(
        1 for item in releases
        if item.get("status") == "packaged"
    ),
    "approved": sum(
        1 for item in releases
        if item.get("status") == "approved"
    ),
    "active": sum(
        1 for item in releases
        if item.get("status") == "active"
    ),
}

registry["last_updated_at"] = now()
save_json(registry_path, registry)

print(json.dumps({
    "success": True,
    "status": "packaged_release_available",
    "release_count": len(releases),
    "latest_release": releases[-1].get("release_id") if releases else None,
}, indent=2))
PY

echo "[2/7] Creating approval manager..."

cat > "$AGENTS/release_approval_manager.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"
RELEASES = ROOT / "releases"

CONFIG = MEMORY / "release_approval_config.json"
REGISTRY = MEMORY / "release_registry.json"
AUDIT = MEMORY / "release_approval_audit.json"
STATE = MEMORY / "release_activation_state.json"
HEALTH = MEMORY / "release_approval_health.json"


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


def latest_release() -> tuple[dict[str, Any], dict[str, Any]]:
    store = load_json(REGISTRY, {})
    releases = store.get("releases", [])
    if not releases:
        raise RuntimeError("No packaged release found")
    return store, releases[-1]


def update_stats(store: dict[str, Any]) -> None:
    releases = store.get("releases", [])
    store["statistics"] = {
        "total": len(releases),
        "ready": sum(
            1 for item in releases
            if item.get("status") in {"packaged", "approved", "active"}
        ),
        "blocked": sum(
            1 for item in releases if item.get("status") == "blocked"
        ),
        "packaged": sum(
            1 for item in releases if item.get("status") == "packaged"
        ),
        "approved": sum(
            1 for item in releases if item.get("status") == "approved"
        ),
        "active": sum(
            1 for item in releases if item.get("status") == "active"
        ),
    }
    store["last_updated_at"] = now()


def approve_latest(reason: str | None = None) -> dict[str, Any]:
    store, release = latest_release()

    if release.get("status") not in {"packaged", "approved"}:
        result = {
            "success": False,
            "status": "release_approval_blocked",
            "reason": f"Release status is {release.get('status')}",
        }
        audit("approve", result)
        return result

    release["status"] = "approved"
    release["owner_approved"] = True
    release["owner_approval_reason"] = reason
    release["approved_at"] = now()
    release["updated_at"] = now()

    update_stats(store)
    save_json(REGISTRY, store)

    result = {
        "success": True,
        "status": "release_approved",
        "release_id": release.get("release_id"),
        "reason": reason,
        "automatic_local_activation": False,
        "automatic_external_deployment": False,
        "automatic_publication": False,
        "automatic_spending": False,
    }

    audit("approve", result)
    return result


def activate_latest() -> dict[str, Any]:
    store, release = latest_release()

    if release.get("status") not in {"approved", "active"}:
        result = {
            "success": False,
            "status": "local_activation_blocked",
            "reason": "Release must be owner-approved first",
            "current_status": release.get("status"),
        }
        audit("activate", result)
        return result

    source = Path(str(release.get("directory", "")))

    if not source.exists():
        result = {
            "success": False,
            "status": "release_directory_missing",
            "directory": str(source),
        }
        audit("activate", result)
        return result

    active_root = RELEASES / "active"

    if active_root.exists():
        shutil.rmtree(active_root)

    shutil.copytree(source, active_root)

    release["status"] = "active"
    release["active_directory"] = str(active_root)
    release["activated_at"] = now()
    release["updated_at"] = now()

    update_stats(store)
    save_json(REGISTRY, store)

    state = {
        "active_release_id": release.get("release_id"),
        "active_directory": str(active_root),
        "activated_at": now(),
        "status": "active",
        "preview_command": f"python {active_root / 'server.py'}",
        "preview_url": "http://127.0.0.1:8765",
        "external_deployment": False,
        "external_publication": False,
    }

    save_json(STATE, state)
    save_json(
        HEALTH,
        {
            "healthy": True,
            "active_release_id": release.get("release_id"),
            "active_directory": str(active_root),
            "last_error": None,
            "updated_at": now(),
        },
    )

    result = {
        "success": True,
        "status": "release_locally_activated",
        "release_id": release.get("release_id"),
        "active_directory": str(active_root),
        "preview_command": state["preview_command"],
        "preview_url": state["preview_url"],
        "automatic_external_deployment": False,
        "automatic_publication": False,
        "automatic_spending": False,
    }

    audit("activate", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    store = load_json(REGISTRY, {})
    state = load_json(STATE, {})
    health = load_json(HEALTH, {})

    result = {
        "success": True,
        "status": "release_approval_status",
        "enabled": config.get("enabled", False),
        "owner_approval_required": config.get("owner_approval_required", True),
        "automatic_release_approval": config.get(
            "automatic_release_approval", False
        ),
        "automatic_local_activation": config.get(
            "automatic_local_activation", False
        ),
        "automatic_external_deployment": config.get(
            "automatic_external_deployment", False
        ),
        "automatic_publication": config.get("automatic_publication", False),
        "automatic_spending": config.get("automatic_spending", False),
        "release_statistics": store.get("statistics", {}),
        "activation_state": state,
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
        if action == "approve-latest":
            reason = " ".join(sys.argv[2:]).strip() or None
            return print_result(approve_latest(reason))

        if action == "activate-latest":
            return print_result(activate_latest())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_release_approval_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "release_approval_error",
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
PY

chmod +x "$AGENTS/release_approval_manager.py"

cat > "$CTL/releaseapprovalctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "release_approval_manager.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root,
    )
)
PY

chmod +x "$CTL/releaseapprovalctl"

echo "[3/7] Compiling..."
python -m py_compile \
  "$AGENTS/release_approval_manager.py" \
  "$CTL/releaseapprovalctl"

echo "[4/7] Resetting latest release to packaged for gate test..."

python - <<'PY'
import json
from pathlib import Path

path = Path.home() / "companyos" / "ceo_memory" / "release_registry.json"
data = json.loads(path.read_text(encoding="utf-8"))
releases = data.get("releases", [])

if not releases:
    raise SystemExit("ERROR: No release available.")

latest = releases[-1]
latest["status"] = "packaged"
latest["owner_approved"] = False
latest.pop("approved_at", None)
latest.pop("activated_at", None)
latest.pop("active_directory", None)

stats = data.setdefault("statistics", {})
stats["total"] = len(releases)
stats["packaged"] = sum(1 for item in releases if item.get("status") == "packaged")
stats["approved"] = sum(1 for item in releases if item.get("status") == "approved")
stats["active"] = sum(1 for item in releases if item.get("status") == "active")

path.write_text(json.dumps(data, indent=2), encoding="utf-8")
print("Latest release reset to packaged.")
PY

echo "[5/7] Testing approval gate..."

set +e
BLOCKED_OUTPUT="$(
  python "$CTL/releaseapprovalctl" activate-latest 2>&1
)"
BLOCKED_CODE=$?
set -e

echo "$BLOCKED_OUTPUT"

if [ "$BLOCKED_CODE" -eq 0 ]; then
  echo "ERROR: Unapproved release was not blocked."
  exit 1
fi

if ! printf '%s' "$BLOCKED_OUTPUT" | grep -q '"status": "local_activation_blocked"'; then
  echo "ERROR: Expected local_activation_blocked result."
  exit 1
fi

echo "Unapproved local activation correctly blocked."

echo "[6/7] Checking status..."
python "$CTL/releaseapprovalctl" status

echo "[7/7] Verifying..."

python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "release_approval_manager.py",
    root / "companyos" / "releaseapprovalctl",
    root / "ceo_memory" / "release_approval_config.json",
    root / "ceo_memory" / "release_registry.json",
    root / "ceo_memory" / "release_activation_state.json",
]

for path in required:
    if not path.exists():
        errors.append(f"Missing: {path}")

for path in required[:2]:
    try:
        py_compile.compile(str(path), doraise=True)
    except Exception as exc:
        errors.append(f"Compile error: {exc}")

try:
    config = json.loads(required[2].read_text(encoding="utf-8"))
    for field in [
        "automatic_release_approval",
        "automatic_local_activation",
        "automatic_external_deployment",
        "automatic_publication",
        "automatic_spending",
    ]:
        if config.get(field) is not False:
            errors.append(f"{field} must remain disabled")
except Exception as exc:
    errors.append(f"Config error: {exc}")

try:
    releases = json.loads(
        required[3].read_text(encoding="utf-8")
    ).get("releases", [])

    if not releases:
        errors.append("No packaged release available")
    elif releases[-1].get("status") != "packaged":
        errors.append("Latest release is not awaiting approval")
except Exception as exc:
    errors.append(f"Release registry error: {exc}")

try:
    state = json.loads(required[4].read_text(encoding="utf-8"))
    if state.get("status") != "inactive":
        errors.append("Release activated before owner approval")
except Exception as exc:
    errors.append(f"Activation state error: {exc}")

print("--------------------------------------------")
print("Phase 15 Step 9 repair verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print(f"ERROR: {error}")

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 15 STEP 9 REPAIR INSTALLED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Do not approve yet."
echo
echo "Commands:"
echo "  python companyos/releaseapprovalctl status"
echo "  python companyos/releaseapprovalctl approve-latest \"Owner approved local release\""
echo "  python companyos/releaseapprovalctl activate-latest"
