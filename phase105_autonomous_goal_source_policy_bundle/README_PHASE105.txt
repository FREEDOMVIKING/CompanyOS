PHASE 105 — AUTONOMOUS GOAL SOURCE POLICY

Adds a policy gate in front of the Phase 103/104 autonomous goal intake path.

FLOW:
incoming goal
 -> normalize
 -> classify source
 -> detect external-action intent
 -> detect financial-action intent
 -> mark approval requirement
 -> durable Phase 103 intake

Internal goals:
accepted normally.

Goals implying external or financial action:
accepted into the durable inbox, but marked:
requires_human_approval = true

This phase does not itself execute those actions.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase105_autonomous_goal_source_policy_bundle
mkdir -p phase105_autonomous_goal_source_policy_bundle

unzip -o ~/storage/downloads/PHASE105_AUTONOMOUS_GOAL_SOURCE_POLICY_BUNDLE.zip \
  -d ~/companyos/phase105_autonomous_goal_source_policy_bundle

python ~/companyos/phase105_autonomous_goal_source_policy_bundle/phase105_install.py

VERIFY:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase105_autonomous_goal_source_policy_bundle/phase105_verify.py

TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase105_policy_test.py

SAFE INTERNAL GOAL EXAMPLE:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase105_runtime_goal_submit.py \
"research and plan an internal software product" \
--priority 50
