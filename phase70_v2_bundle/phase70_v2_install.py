#!/usr/bin/env python3
from pathlib import Path
import ast, json, py_compile, shutil, os
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase70_v2_bundle"
FILES = {
    BUNDLE / "launch_controller.py": ROOT / "companyos/runtime/launch_controller.py",
    BUNDLE / "phase70_practice_run.py": ROOT / "phase70_practice_run.py",
    BUNDLE / "phase70_status.py": ROOT / "phase70_status.py",
    BUNDLE / "phase70_stop.py": ROOT / "phase70_stop.py",
}
MANIFEST = ROOT / "PHASE70_V2_INSTALLED.json"

def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backups = {}
    for src, dst in FILES.items():
        if dst.exists():
            b = dst.with_name(dst.name + f".phase70_v2_backup_{stamp}")
            shutil.copy2(dst, b)
            backups[str(dst)] = str(b)
        text = src.read_text(encoding="utf-8")
        ast.parse(text)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text, encoding="utf-8")
        py_compile.compile(str(dst), doraise=True)

    manifest = {
        "phase": "70_V2",
        "status": "installed",
        "backups": backups,
        "practice_run_available": True,
        "practice_broadcasts_enabled": False,
        "blanket_restrictions_added": False,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("PHASE70_V2_LAUNCH_CONTROLLER: INSTALLED")
    print("COMPILE_CHECK: PASS")
    print("PRACTICE_RUN_AVAILABLE: True")
    print("PRACTICE_BROADCASTS_ENABLED: False")
    print("BLANKET_RESTRICTIONS_ADDED: False")

if __name__ == "__main__":
    main()
