from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass(frozen=True)
class TermuxBootStatus:
    boot_dir: str
    boot_script: str
    boot_script_present: bool
    boot_script_executable: bool
    service_ctl_present: bool
    auto_start_configured: bool
    reason: str


class TermuxBootManager:
    """
    Manages a Termux:Boot-compatible launcher for CompanyOS.

    The generated boot script:
    - waits briefly for Android/Termux storage/network startup
    - changes into ~/companyos
    - invokes the Phase 92 runtime service manager
    - starts supervisor + watchdog only
    - does NOT directly build/sign/broadcast transactions
    """

    def __init__(self) -> None:
        self.home = Path.home()
        self.companyos = self.home / "companyos"
        self.boot_dir = self.home / ".termux" / "boot"
        self.boot_script = self.boot_dir / "companyos_start.sh"
        self.service_ctl = self.companyos / "phase92_runtime_service_ctl.py"

    def script_text(self) -> str:
        return """#!/data/data/com.termux/files/usr/bin/bash
set -u

sleep 20

cd "$HOME/companyos" || exit 1

export PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos"

python phase92_runtime_service_ctl.py start \
  --supervisor-interval 15 \
  --watchdog-check-every 30 \
  --max-failures 5 \
  --restart-backoff 5 \
  >> "$HOME/.companyos_runtime/termux_boot.log" 2>&1
"""

    def install(self) -> TermuxBootStatus:
        self.boot_dir.mkdir(parents=True, exist_ok=True)
        self.boot_script.write_text(self.script_text(), encoding="utf-8")
        self.boot_script.chmod(0o700)
        return self.status()

    def status(self) -> TermuxBootStatus:
        present = self.boot_script.exists()
        executable = bool(present and (self.boot_script.stat().st_mode & 0o111))
        service_ctl_present = self.service_ctl.exists()
        configured = present and executable and service_ctl_present

        if configured:
            reason = "termux_boot_launcher_ready"
        elif not service_ctl_present:
            reason = "phase92_service_ctl_missing"
        elif not present:
            reason = "boot_script_missing"
        elif not executable:
            reason = "boot_script_not_executable"
        else:
            reason = "not_ready"

        return TermuxBootStatus(
            boot_dir=str(self.boot_dir),
            boot_script=str(self.boot_script),
            boot_script_present=present,
            boot_script_executable=executable,
            service_ctl_present=service_ctl_present,
            auto_start_configured=configured,
            reason=reason,
        )
