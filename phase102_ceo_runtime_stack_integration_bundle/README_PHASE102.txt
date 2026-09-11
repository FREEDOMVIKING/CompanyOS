PHASE 102 — CEO RUNTIME STACK INTEGRATION

This phase combines:

PHASE 92
financial/runtime supervisor + watchdog service stack

WITH

PHASE 101
autonomous CEO runtime service

Into one unified control plane.

START:
- ensure financial/runtime stack is healthy
- then start autonomous CEO runtime
- prevent duplicate CEO runtime instances

STATUS:
- financial supervisor state
- watchdog state
- CEO runtime state
- orchestration counters
- unified readiness

STOP:
- stop CEO runtime first
- stop watchdog/supervisor stack second

This manager itself performs no external actions and no financial transaction
signing/broadcasting.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase102_ceo_runtime_stack_integration_bundle
mkdir -p phase102_ceo_runtime_stack_integration_bundle

unzip -o ~/storage/downloads/PHASE102_CEO_RUNTIME_STACK_INTEGRATION_BUNDLE.zip \
  -d ~/companyos/phase102_ceo_runtime_stack_integration_bundle

python ~/companyos/phase102_ceo_runtime_stack_integration_bundle/phase102_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase102_ceo_runtime_stack_integration_bundle/phase102_verify.py

TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase102_unified_runtime_test.py

START UNIFIED STACK:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase102_unified_runtime_ctl.py start \
  --financial-supervisor-interval 15 \
  --watchdog-check-every 30 \
  --financial-max-failures 5 \
  --restart-backoff 5 \
  --ceo-interval 10 \
  --ceo-max-failures 5

STATUS:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase102_unified_runtime_ctl.py status

STOP:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase102_unified_runtime_ctl.py stop
