PHASE 93 — TERMUX BOOT AUTO-START

Purpose:
Create a Termux:Boot-compatible launcher so CompanyOS can bring up the
Phase 92 runtime service stack after the phone restarts.

Generated launcher:
~/.termux/boot/companyos_start.sh

It starts:
- Phase 89 runtime supervisor
- Phase 91 watchdog
through the Phase 92 service manager.

It does NOT directly build, sign, or broadcast transactions.

IMPORTANT:
Android requires the separate Termux:Boot app/plugin for ~/.termux/boot scripts
to run automatically after device reboot.

INSTALL BUNDLE:
cd ~/companyos || exit 1
rm -rf phase93_termux_boot_autostart_bundle
mkdir -p phase93_termux_boot_autostart_bundle

unzip -o ~/storage/downloads/PHASE93_TERMUX_BOOT_AUTOSTART_BUNDLE.zip \
  -d ~/companyos/phase93_termux_boot_autostart_bundle

python ~/companyos/phase93_termux_boot_autostart_bundle/phase93_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase93_termux_boot_autostart_bundle/phase93_verify.py

DRY RUN TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase93_boot_dry_run_test.py

CREATE REAL BOOT LAUNCHER:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase93_boot_ctl.py install

CHECK STATUS:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase93_boot_ctl.py status
