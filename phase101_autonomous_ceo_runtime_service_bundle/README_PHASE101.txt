PHASE 101 — AUTONOMOUS CEO RUNTIME SERVICE

Builds directly on Phase 100.

Purpose:
Turn the Phase 100 CEO orchestrator into a continuously runnable internal service.

Each service tick:
- discovers persisted RUNNING orchestrations
- advances each one by at most one CEO cycle
- persists service health
- journals decisions/errors
- isolates failures between orchestrations
- enforces a max-consecutive-failure stop guard

This remains INTERNAL autonomy only.

It does NOT:
- send messages/emails
- publish
- purchase
- deploy externally
- move money
- sign transactions
- broadcast transactions

INSTALL:
cd ~/companyos || exit 1
rm -rf phase101_autonomous_ceo_runtime_service_bundle
mkdir -p phase101_autonomous_ceo_runtime_service_bundle

unzip -o ~/storage/downloads/PHASE101_AUTONOMOUS_CEO_RUNTIME_SERVICE_BUNDLE.zip \
  -d ~/companyos/phase101_autonomous_ceo_runtime_service_bundle

python ~/companyos/phase101_autonomous_ceo_runtime_service_bundle/phase101_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase101_autonomous_ceo_runtime_service_bundle/phase101_verify.py

ONE COMPLETE ISOLATED TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase101_ceo_runtime_once.py

CHECK PERSISTED RUNTIME STATUS:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase101_ceo_runtime_status.py

RUN CONTINUOUS CEO RUNTIME:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase101_ceo_runtime_run.py --interval 10 --max-failures 5
