PHASE 97 — AUTONOMOUS GOAL EXECUTION LOOP

Builds on Phases 94–96.

Adds a continuously runnable internal loop that:
- recovers stale tasks
- finds dependency-ready work
- routes it to the correct specialist
- persists COMPLETED/FAILED state
- advances the next stage automatically

Current internal flow:
research -> planning -> build

The loop itself never signs or broadcasts transactions.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase97_autonomous_goal_execution_loop_bundle
mkdir -p phase97_autonomous_goal_execution_loop_bundle

unzip -o ~/storage/downloads/PHASE97_AUTONOMOUS_GOAL_EXECUTION_LOOP_BUNDLE.zip \
  -d ~/companyos/phase97_autonomous_goal_execution_loop_bundle

python ~/companyos/phase97_autonomous_goal_execution_loop_bundle/phase97_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase97_autonomous_goal_execution_loop_bundle/phase97_verify.py

TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase97_goal_loop_test.py

RUN ONE REAL QUEUE CYCLE:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase97_runtime_goal_loop_once.py

RUN CONTINUOUS INTERNAL GOAL LOOP:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase97_runtime_goal_loop_run.py --interval 10
