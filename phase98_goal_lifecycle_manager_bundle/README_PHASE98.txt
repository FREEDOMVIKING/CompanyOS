PHASE 98 — GOAL LIFECYCLE MANAGER

Builds on Phases 94–97.

Adds CEO-level goal state:
ACTIVE
EXECUTING
BLOCKED
COMPLETED
FAILED

Capabilities:
- tracks all tasks belonging to one goal
- counts queued/running/completed/failed work
- detects blocked goals
- aggregates specialist outputs into a final CEO-level result
- persists goal lifecycle state

The goal lifecycle manager never signs or broadcasts transactions.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase98_goal_lifecycle_manager_bundle
mkdir -p phase98_goal_lifecycle_manager_bundle

unzip -o ~/storage/downloads/PHASE98_GOAL_LIFECYCLE_MANAGER_BUNDLE.zip \
  -d ~/companyos/phase98_goal_lifecycle_manager_bundle

python ~/companyos/phase98_goal_lifecycle_manager_bundle/phase98_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase98_goal_lifecycle_manager_bundle/phase98_verify.py

TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase98_goal_lifecycle_test.py

CHECK A REAL GOAL:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase98_runtime_goal_status.py "<GOAL_ID>"
