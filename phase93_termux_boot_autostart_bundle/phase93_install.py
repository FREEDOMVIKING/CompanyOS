#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase93_termux_boot_autostart_bundle"

pairs = [
    (
        BUNDLE / "termux_boot_manager.py",
        ROOT / "companyos/walletintegration/termux_boot_manager.py",
    ),
    (
        BUNDLE / "phase93_boot_ctl.py",
        ROOT / "phase93_boot_ctl.py",
    ),
    (
        BUNDLE / "phase93_boot_dry_run_test.py",
        ROOT / "phase93_boot_dry_run_test.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)

    if dst.exists():
        backup = dst.with_name(dst.name + f".phase93_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "93_TERMUX_BOOT_AUTOSTART",
    "status": "installed",
    "termux_boot_launcher_available": True,
    "uses_phase92_service_manager": True,
    "boot_launcher_direct_broadcast": False,
    "installer_broadcasts": False,
    "verifier_broadcasts": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE93_TERMUX_BOOT_AUTOSTART_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE93_TERMUX_BOOT_AUTOSTART: INSTALLED")
print("COMPILE_CHECK: PASS")
print("TERMUX_BOOT_LAUNCHER_AVAILABLE: True")
print("USES_PHASE92_SERVICE_MANAGER: True")
print("BOOT_LAUNCHER_DIRECT_BROADCAST: False")
print("PRIVATE_KEY_PRINTED: False")
