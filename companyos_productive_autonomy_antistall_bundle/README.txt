COMPANYOS PRODUCTIVE AUTONOMY / ANTI-STALL BUNDLE

Purpose
-------
CompanyOS can be healthy and still spend too many cycles with zero active orchestrations.
This bundle adds a watchdog that detects prolonged idle cycling and starts a concrete,
reversible INTERNAL goal through the existing AutonomousCEOOrchestrator public API.

It does NOT:
- bypass consequential external-action approvals
- bypass transaction / financial controls
- change wallet keys
- change FULL_LIVE limits
- remove signer, reserve, allowlist, or reconciliation controls

Default behavior
----------------
Every 30 seconds it checks runtime state.
When all of these are true:
- runtime is running and ready
- active_orchestrations == 0
- at least 25 additional cycles have occurred without completed-orchestration progress
- at least 120 seconds passed without completion progress
- fewer than 3 anti-stall starts occurred in the last hour

...it starts one high-priority internal goal designed to produce concrete work rather than more review.

Install
-------
cd ~/companyos
rm -rf companyos_productive_autonomy_antistall_bundle
mkdir -p companyos_productive_autonomy_antistall_bundle

unzip -o ~/storage/downloads/COMPANYOS_PRODUCTIVE_AUTONOMY_ANTISTALL_BUNDLE.zip   -d ~/companyos/companyos_productive_autonomy_antistall_bundle

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_productive_autonomy_antistall_bundle/install.py

python companyos_productive_autonomy_antistall_bundle/verify.py

Start
-----
bash scripts/companyos_productive_autonomy.sh start

Status
------
bash scripts/companyos_productive_autonomy.sh status

One-time test
-------------
bash scripts/companyos_productive_autonomy.sh once

Logs
----
bash scripts/companyos_productive_autonomy.sh logs

Fixed final-launch wrapper
--------------------------
bash scripts/companyos_final_launch_fixed.sh status

Optional tuning (defaults shown)
--------------------------------
export COMPANYOS_ANTISTALL_IDLE_CYCLES=25
export COMPANYOS_ANTISTALL_MIN_SECONDS=120
export COMPANYOS_ANTISTALL_MAX_STARTS_PER_HOUR=3
export COMPANYOS_ANTISTALL_INTERVAL_SECONDS=30
