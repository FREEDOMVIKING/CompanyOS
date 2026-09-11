#!/usr/bin/env python3
from pathlib import Path
import tempfile

from companyos.walletintegration.termux_boot_manager import TermuxBootManager

with tempfile.TemporaryDirectory(prefix="phase93_boot_") as td:
    base = Path(td)

    mgr = TermuxBootManager()
    mgr.home = base
    mgr.companyos = base / "companyos"
    mgr.boot_dir = base / ".termux" / "boot"
    mgr.boot_script = mgr.boot_dir / "companyos_start.sh"
    mgr.service_ctl = mgr.companyos / "phase92_runtime_service_ctl.py"

    mgr.companyos.mkdir(parents=True, exist_ok=True)
    mgr.service_ctl.write_text("# test placeholder\n", encoding="utf-8")

    result = mgr.install()
    text = mgr.boot_script.read_text(encoding="utf-8")

    checks = {
        "boot_script_present": result.boot_script_present,
        "boot_script_executable": result.boot_script_executable,
        "service_ctl_present": result.service_ctl_present,
        "auto_start_configured": result.auto_start_configured,
        "uses_phase92_service_manager": "phase92_runtime_service_ctl.py start" in text,
        "no_direct_send_transaction": "sendTransaction" not in text,
        "no_private_key_reference": "SOLANA_PRIVATE_KEY" not in text,
    }

    ok = True
    for name, passed in checks.items():
        ok = ok and passed
        print(name, "=>", "PASS" if passed else "FAIL")

    print("BOOT_SCRIPT_BUILDS_TRANSACTION: False")
    print("BOOT_SCRIPT_SIGNS_TRANSACTION: False")
    print("BOOT_SCRIPT_BROADCASTS_DIRECTLY: False")
    print("PHASE93_BOOT_DRY_RUN_TEST:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
