COMPANYOS CONSOLIDATION BUNDLE 5
Canonical Daemon + Crash Recovery + Operational Control

Purpose
-------
This bundle turns the canonical production runtime from Bundle 4 into a resilient,
single-instance background service suitable for long-running Termux operation.

Adds:
- canonical daemon wrapper
- single-instance PID/lock protection
- crash/restart backoff
- heartbeat/state files
- log rotation
- start/stop/status/restart/logs CLI
- stale PID cleanup
- graceful shutdown handling
- autostart-ready launcher script (NOT enabled automatically)

Does NOT:
- enable transaction broadcasting
- enable external actions
- modify wallet keys
- delete legacy runtimes
- install Android boot autostart automatically
- bypass approval/treasury/live gates

Install:
  cd ~/companyos
  unzip -o ~/storage/downloads/COMPANYOS_CONSOLIDATION_BUNDLE_5.zip \
    -d ~/companyos/companyos_consolidation_bundle_5

  PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
  python companyos_consolidation_bundle_5/install.py

Verify:
  PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
  python companyos_consolidation_bundle_5/verify.py

Smoke:
  PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
  python companyos_consolidation_bundle_5/smoke_test.py

Service control:
  bash scripts/companyos_service.sh start
  bash scripts/companyos_service.sh status
  bash scripts/companyos_service.sh restart
  bash scripts/companyos_service.sh stop
  bash scripts/companyos_service.sh logs
