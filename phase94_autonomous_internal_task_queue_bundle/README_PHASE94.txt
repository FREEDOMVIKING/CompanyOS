PHASE 94 — AUTONOMOUS INTERNAL TASK QUEUE

Adds a persistent internal work queue for CompanyOS.

Capabilities:
- durable task records
- priority ordering
- idempotency-key duplicate protection
- CLAIMED / RUNNING / COMPLETED / FAILED lifecycle
- retries with delay
- stale worker recovery after restart/crash

The task queue itself never signs or broadcasts transactions.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase94_autonomous_internal_task_queue_bundle
mkdir -p phase94_autonomous_internal_task_queue_bundle

unzip -o ~/storage/downloads/PHASE94_AUTONOMOUS_INTERNAL_TASK_QUEUE_BUNDLE.zip \
  -d ~/companyos/phase94_autonomous_internal_task_queue_bundle

python ~/companyos/phase94_autonomous_internal_task_queue_bundle/phase94_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase94_autonomous_internal_task_queue_bundle/phase94_verify.py

TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase94_task_queue_test.py

RUNTIME QUEUE STATUS:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase94_runtime_task_queue_status.py
