PHASE 95 — AUTONOMOUS TASK DISPATCHER + SPECIALIST ROUTING

Builds on Phase 94.

Adds:
- priority-based task dispatch
- specialist routing by task_type
- task ownership assignment
- RUNNING -> COMPLETED/FAILED persistence
- retry path through the Phase 94 queue

Default validation specialists:
- research_agent
- planning_agent
- builder_agent

These Phase 95 default handlers are deterministic internal validation stubs.
Later phases can connect them to the existing CompanyOS specialist-agent system.

The dispatcher itself never signs or broadcasts transactions.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase95_autonomous_task_dispatcher_bundle
mkdir -p phase95_autonomous_task_dispatcher_bundle

unzip -o ~/storage/downloads/PHASE95_AUTONOMOUS_TASK_DISPATCHER_BUNDLE.zip \
  -d ~/companyos/phase95_autonomous_task_dispatcher_bundle

python ~/companyos/phase95_autonomous_task_dispatcher_bundle/phase95_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase95_autonomous_task_dispatcher_bundle/phase95_verify.py

TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase95_dispatcher_test.py

RUNTIME DISPATCH ONE QUEUED TASK:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase95_runtime_dispatch_once.py
