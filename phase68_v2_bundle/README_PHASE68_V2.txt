PHASE 68 V2 — HEALTH + STARTUP RECOVERY AUTOMATION

This phase deliberately avoids blanket restrictions.

What it adds:
- startup recovery pass
- health supervisor
- heartbeat/status files
- optional watchdog loop
- stale pending visibility
- automatic read-only reconciliation

Autonomy design:
- internal/reversible work remains available under existing CompanyOS logic
- research/planning/building/learning are not restricted by Phase 68
- existing controls for irreversible external/financial actions are preserved
- no automatic transaction rebroadcasts are added

Install:
cd ~/storage/downloads || exit 1
unzip -o PHASE68_V2_HEALTH_RECOVERY_AUTOMATION_BUNDLE.zip -d ~/companyos/phase68_v2_bundle
cd ~/companyos || exit 1
python phase68_v2_bundle/phase68_v2_install.py

Verify:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python phase68_v2_bundle/phase68_v2_verify.py

Run one startup recovery pass:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python phase68_startup_recover.py

Check health:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python phase68_health.py

Watchdog:
bash ~/companyos/phase68_watchdog.sh

Default watchdog interval is 300 seconds.
Override:
COMPANYOS_HEALTH_INTERVAL_SECONDS=600 bash ~/companyos/phase68_watchdog.sh
