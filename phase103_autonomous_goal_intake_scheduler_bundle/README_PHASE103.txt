PHASE 103 — AUTONOMOUS GOAL INTAKE + SCHEDULER

Purpose:
Give the running autonomous CEO stack a durable inbox for new high-level goals.

FLOW:

GOAL INBOX
  -> priority scheduling
  -> durable claim
  -> Phase 100 orchestration creation
  -> Phase 101 CEO runtime advancement

Adds:
- persistent CEO goal intake records
- priority ordering
- restart recovery for CLAIMED intake records
- intake -> orchestration bridge
- one-command intake submission
- one-cycle scheduler/bridge tools

No external actions are performed by this phase.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase103_autonomous_goal_intake_scheduler_bundle
mkdir -p phase103_autonomous_goal_intake_scheduler_bundle

unzip -o ~/storage/downloads/PHASE103_AUTONOMOUS_GOAL_INTAKE_SCHEDULER_BUNDLE.zip \
  -d ~/companyos/phase103_autonomous_goal_intake_scheduler_bundle

python ~/companyos/phase103_autonomous_goal_intake_scheduler_bundle/phase103_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase103_autonomous_goal_intake_scheduler_bundle/phase103_verify.py

TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase103_goal_intake_test.py

SUBMIT A REAL INTERNAL GOAL:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase103_runtime_goal_intake_submit.py \
"research and develop an internal digital product opportunity" \
--priority 50

PROCESS ONE INTAKE:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase103_runtime_goal_scheduler_once.py

OR PROCESS + ADVANCE CEO RUNTIME ONE CYCLE:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase103_runtime_intake_bridge_once.py

STATUS:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase103_goal_intake_status.py
