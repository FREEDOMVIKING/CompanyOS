PHASE 104 — CONTINUOUS AUTONOMOUS GOAL INTAKE RUNTIME

Adds a persistent runtime loop on top of Phase 103.

FLOW:
durable goal inbox
 -> priority scheduler
 -> CEO orchestration
 -> CEO runtime cycle
 -> repeat

INSTALL:
cd ~/companyos || exit 1
rm -rf phase104_continuous_goal_intake_runtime_bundle
mkdir -p phase104_continuous_goal_intake_runtime_bundle
unzip -o ~/storage/downloads/PHASE104_CONTINUOUS_GOAL_INTAKE_RUNTIME_BUNDLE.zip \
  -d ~/companyos/phase104_continuous_goal_intake_runtime_bundle
python ~/companyos/phase104_continuous_goal_intake_runtime_bundle/phase104_install.py

VERIFY:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase104_continuous_goal_intake_runtime_bundle/phase104_verify.py

TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python phase104_test.py

ONE SAFE CYCLE:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python phase104_runtime_ctl.py once

START BACKGROUND LOOP:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase104_runtime_ctl.py start --interval 10 --max-failures 5

STATUS:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python phase104_runtime_ctl.py status

STOP:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python phase104_runtime_ctl.py stop

This phase performs no external actions and does not sign or broadcast transactions.
