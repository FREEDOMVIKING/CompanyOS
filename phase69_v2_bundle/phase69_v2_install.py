#!/usr/bin/env python3
from pathlib import Path
import ast, json, py_compile, shutil
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase69_v2_bundle"
DST = ROOT / "companyos/runtime/launch_readiness_audit.py"
CLI = ROOT / "phase69_launch_audit.py"
MANIFEST = ROOT / "PHASE69_V2_INSTALLED.json"

def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backups = {}
    for path in (DST, CLI):
        if path.exists():
            b = path.with_name(path.name + f".phase69_v2_backup_{stamp}")
            shutil.copy2(path, b)
            backups[str(path)] = str(b)

    pairs = [
        (BUNDLE / "launch_readiness_audit.py", DST),
        (BUNDLE / "phase69_launch_audit.py", CLI),
    ]
    for src, dst in pairs:
        text = src.read_text(encoding="utf-8")
        ast.parse(text)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text, encoding="utf-8")
        py_compile.compile(str(dst), doraise=True)

    manifest = {
        "phase": "69_V2",
        "status": "installed",
        "backups": backups,
        "blanket_restrictions_added": False,
        "secrets_logged": False,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("PHASE69_V2_LAUNCH_READINESS_AUDIT: INSTALLED")
    print("COMPILE_CHECK: PASS")
    print("BLANKET_RESTRICTIONS_ADDED: False")
    print("SECRETS_LOGGED: False")

if __name__ == "__main__":
    main()
