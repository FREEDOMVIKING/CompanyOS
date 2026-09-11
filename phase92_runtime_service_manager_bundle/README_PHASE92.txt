PHASE 92 — RUNTIME SERVICE MANAGER

Adds one control layer above Phase 90 + Phase 91.

START:
- ensures runtime supervisor is running
- ensures watchdog is running
- blocks startup if unresolved SUBMITTED records exist
- avoids duplicate watchdog processes

STATUS:
- supervisor running/ready/RPC/stale
- unresolved transaction count
- watchdog running
- combined service readiness

STOP:
- stops watchdog first
- then stops supervisor

This service manager never builds, signs, authorizes, or broadcasts transactions.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase92_runtime_service_manager_bundle
mkdir -p phase92_runtime_service_manager_bundle

unzip -o ~/storage/downloads/PHASE92_RUNTIME_SERVICE_MANAGER_BUNDLE.zip \
  -d ~/companyos/phase92_runtime_service_manager_bundle

python ~/companyos/phase92_runtime_service_manager_bundle/phase92_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase92_runtime_service_manager_bundle/phase92_verify.py

TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase92_service_manager_test.py

START FULL RUNTIME STACK:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase92_runtime_service_ctl.py start \
  --supervisor-interval 15 \
  --watchdog-check-every 30 \
  --max-failures 5 \
  --restart-backoff 5

STATUS:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase92_runtime_service_ctl.py status

STOP FULL STACK:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase92_runtime_service_ctl.py stop

WATCHDOG LOG:
tail -f ~/.companyos_runtime/runtime_watchdog.log
