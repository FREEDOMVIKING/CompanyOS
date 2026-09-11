#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEMORY="$ROOT/ceo_memory"
EXPORTS="$ROOT/exports"
RELEASES="$ROOT/releases"
BACKUP="$ROOT/backups/phase15_step10_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEMORY" "$EXPORTS" "$RELEASES" "$BACKUP"

echo "============================================================"
echo " Phase 15 Step 10 - Product Packaging and Export Engine"
echo "============================================================"

for file in \
  "$AGENTS/product_packager.py" \
  "$CTL/packagectl" \
  "$MEMORY/product_packager_config.json" \
  "$MEMORY/product_export_registry.json" \
  "$MEMORY/product_packager_health.json"
do
  if [ -f "$file" ]; then
    cp -a "$file" "$BACKUP/"
  fi
done

cat > "$MEMORY/product_packager_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_packaging": false,
  "automatic_version_increment": false,
  "automatic_external_upload": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "owner_approval_required_for_external_distribution": true,
  "default_version": "1.0.0",
  "supported_formats": [
    "web_zip",
    "source_zip",
    "release_tar_gz"
  ]
}
JSON

if [ ! -f "$MEMORY/product_export_registry.json" ]; then
cat > "$MEMORY/product_export_registry.json" <<'JSON'
{
  "schema_version": 1,
  "exports": [],
  "statistics": {
    "total": 0,
    "ready": 0,
    "failed": 0
  },
  "last_updated_at": null
}
JSON
fi

cat > "$AGENTS/product_packager.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"
EXPORTS = ROOT / "exports"
RELEASES = ROOT / "releases"

CONFIG = MEMORY / "product_packager_config.json"
STATE = MEMORY / "release_activation_state.json"
REGISTRY = MEMORY / "product_export_registry.json"
HEALTH = MEMORY / "product_packager_health.json"
AUDIT = MEMORY / "product_packager_audit.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    tmp.replace(path)


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


def safe_name(value: str) -> str:
    text = "".join(
        c.lower() if c.isalnum() else "_"
        for c in value
    )
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("_") or "product"


def active_release() -> tuple[str, Path]:
    state = load_json(STATE, {})
    release_id = state.get("active_release_id")
    directory = Path(str(state.get("active_directory") or ""))

    if not release_id or not directory.exists():
        raise RuntimeError("No active local release found")

    return str(release_id), directory


def latest_export_version(product_id: str) -> str:
    config = load_json(CONFIG, {})
    default = str(config.get("default_version", "1.0.0"))

    records = load_json(REGISTRY, {}).get("exports", [])
    versions = [
        str(item.get("version"))
        for item in records
        if item.get("product_id") == product_id
    ]

    if not versions:
        return default

    parts = versions[-1].split(".")
    try:
        major, minor, patch = [int(x) for x in parts]
        return f"{major}.{minor}.{patch + 1}"
    except Exception:
        return default


def zip_directory(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(
        destination,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for path in source.rglob("*"):
            if path.is_file():
                archive.write(
                    path,
                    arcname=path.relative_to(source),
                )


def build_exports() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {
            "success": False,
            "status": "product_packager_disabled",
        }
        audit("build", result)
        return result

    product_id, source = active_release()
    version = latest_export_version(product_id)

    product_root = EXPORTS / product_id / version
    if product_root.exists():
        shutil.rmtree(product_root)

    product_root.mkdir(parents=True, exist_ok=True)

    web_source = source / "frontend"
    if not web_source.exists():
        raise RuntimeError("Active release frontend directory missing")

    web_zip = product_root / f"{product_id}-web-{version}.zip"
    source_zip = product_root / f"{product_id}-source-{version}.zip"

    zip_directory(web_source, web_zip)
    zip_directory(source, source_zip)

    release_bundle_candidates = list(
        RELEASES.glob(f"{product_id}*.tar.gz")
    )
    release_bundle = (
        release_bundle_candidates[-1]
        if release_bundle_candidates
        else None
    )

    manifest = {
        "product_id": product_id,
        "version": version,
        "status": "ready",
        "formats": {
            "web_zip": str(web_zip),
            "source_zip": str(source_zip),
            "release_tar_gz": (
                str(release_bundle)
                if release_bundle
                else None
            ),
        },
        "files": {
            "web_zip_exists": web_zip.exists(),
            "source_zip_exists": source_zip.exists(),
            "release_tar_gz_exists": (
                release_bundle.exists()
                if release_bundle
                else False
            ),
        },
        "owner_approval_required_for_external_distribution": True,
        "automatic_external_upload": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "created_at": now(),
    }

    manifest_path = product_root / "EXPORT_MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    readme = product_root / "README_EXPORT.txt"
    readme.write_text(
        "CompanyOS Product Export\n\n"
        f"Product: {product_id}\n"
        f"Version: {version}\n\n"
        "web zip: browser-ready frontend files\n"
        "source zip: complete local release source\n"
        "release tar.gz: packaged release bundle when available\n\n"
        "External upload and publication remain disabled.\n",
        encoding="utf-8",
    )

    registry = load_json(
        REGISTRY,
        {
            "schema_version": 1,
            "exports": [],
            "statistics": {},
        },
    )

    records = registry.setdefault("exports", [])
    records.append({
        **manifest,
        "manifest": str(manifest_path),
        "export_directory": str(product_root),
    })

    registry["statistics"] = {
        "total": len(records),
        "ready": sum(
            1 for item in records
            if item.get("status") == "ready"
        ),
        "failed": sum(
            1 for item in records
            if item.get("status") == "failed"
        ),
    }
    registry["last_updated_at"] = now()

    save_json(REGISTRY, registry)
    save_json(
        HEALTH,
        {
            "healthy": True,
            "latest_product_id": product_id,
            "latest_version": version,
            "latest_export_directory": str(product_root),
            "last_error": None,
            "updated_at": now(),
        },
    )

    result = {
        "success": True,
        "status": "product_exports_created",
        "product_id": product_id,
        "version": version,
        "export_directory": str(product_root),
        "web_zip": str(web_zip),
        "source_zip": str(source_zip),
        "release_tar_gz": (
            str(release_bundle)
            if release_bundle
            else None
        ),
        "automatic_external_upload": False,
        "automatic_publication": False,
        "automatic_spending": False,
    }

    audit("build", result)
    return result


def latest() -> dict[str, Any]:
    records = load_json(REGISTRY, {}).get("exports", [])
    result = {
        "success": bool(records),
        "status": "latest_product_export",
        "export": records[-1] if records else None,
    }
    audit("latest", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    registry = load_json(REGISTRY, {})
    health = load_json(HEALTH, {})

    result = {
        "success": True,
        "status": "product_packager_status",
        "enabled": config.get("enabled", False),
        "automatic_packaging": config.get(
            "automatic_packaging", False
        ),
        "automatic_version_increment": config.get(
            "automatic_version_increment", False
        ),
        "automatic_external_upload": config.get(
            "automatic_external_upload", False
        ),
        "automatic_publication": config.get(
            "automatic_publication", False
        ),
        "automatic_spending": config.get(
            "automatic_spending", False
        ),
        "statistics": registry.get("statistics", {}),
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
        if action == "build":
            return print_result(build_exports())

        if action == "latest":
            return print_result(latest())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_packager_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "product_packager_error",
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

chmod +x "$AGENTS/product_packager.py"

cat > "$CTL/packagectl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "product_packager.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root,
    )
)
PY

chmod +x "$CTL/packagectl"

echo "[1/5] Compiling..."
python -m py_compile \
  "$AGENTS/product_packager.py" \
  "$CTL/packagectl"

echo "[2/5] Building export packages..."
python "$CTL/packagectl" build

echo "[3/5] Checking package status..."
python "$CTL/packagectl" status
python "$CTL/packagectl" latest

echo "[4/5] Verifying..."

python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "product_packager.py",
    root / "companyos" / "packagectl",
    root / "ceo_memory" / "product_packager_config.json",
    root / "ceo_memory" / "product_export_registry.json",
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
        "automatic_packaging",
        "automatic_version_increment",
        "automatic_external_upload",
        "automatic_publication",
        "automatic_spending",
    ]:
        if config.get(field) is not False:
            errors.append(f"{field} must remain disabled")

except Exception as exc:
    errors.append(f"Config error: {exc}")

try:
    exports = json.loads(
        required[3].read_text(encoding="utf-8")
    ).get("exports", [])

    if not exports:
        errors.append("No export package was created")
    else:
        latest = exports[-1]

        for field in ["web_zip", "source_zip"]:
            path = Path(str(latest.get("formats", {}).get(field, "")))
            if not path.exists():
                errors.append(f"Missing export file: {path}")
            elif path.stat().st_size <= 0:
                errors.append(f"Empty export file: {path}")

        manifest = Path(str(latest.get("manifest", "")))
        if not manifest.exists():
            errors.append("Export manifest missing")

except Exception as exc:
    errors.append(f"Export registry error: {exc}")

print("--------------------------------------------")
print("Phase 15 Step 10 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print(f"ERROR: {error}")

if errors:
    raise SystemExit(1)
PY

echo "[5/5] Complete."

echo
echo "============================================================"
echo " PHASE 15 STEP 10 INSTALLED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/packagectl build"
echo "  python companyos/packagectl latest"
echo "  python companyos/packagectl status"
echo
echo "Exports:"
echo "  $EXPORTS"
