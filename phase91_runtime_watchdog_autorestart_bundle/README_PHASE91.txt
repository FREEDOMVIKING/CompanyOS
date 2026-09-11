PHASE 91 — RUNTIME WATCHDOG + AUTO-RESTART

Adds a watchdog above the Phase 90 control plane.

Behavior:
- if runtime is healthy -> do nothing
- if runtime is dead/unhealthy -> restart it
- if unresolved SUBMITTED records exist -> DO NOT restart
- rate-limit repeated restart loops
- persist watchdog state

The watchdog never builds, signs, or broadcasts transactions.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase91_runtime_watchdog_autorestart_bundle
mkdir -p phase91_runtime_watchdog_autorestart_bundle

unzip -o ~/storage/downloads/PHASE91_RUNTIME_WATCHDOG_AUTORESTART_BUNDLE.zip \
  -d ~/companyos/phase91_runtime_watchdog_autorestart_bundle

python ~/companyos/phase91_runtime_watchdog_autorestart_bundle/phase91_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase91_runtime_watchdog_autorestart_bundle/phase91_verify.py

ONE WATCHDOG CHECK:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase91_watchdog_once.py --restart-backoff 2

CONTINUOUS WATCHDOG:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase91_watchdog_loop.py \
  --check-every 30 \
  --runtime-interval 15 \
  --max-failures 5 \
  --restart-backoff 5
