PHASE 99 — GOAL OUTCOME EVALUATOR

Builds on Phase 98.

Adds:
- CEO-level evaluation of a goal outcome
- evidence aggregation from specialist task outputs
- deterministic success/failure/blocked assessment
- next-action decision
- follow-up goal suggestion when recovery/replanning is needed
- persistent outcome records

This phase does NOT perform external actions or financial transactions.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase99_goal_outcome_evaluator_bundle
mkdir -p phase99_goal_outcome_evaluator_bundle

unzip -o ~/storage/downloads/PHASE99_GOAL_OUTCOME_EVALUATOR_BUNDLE.zip \
  -d ~/companyos/phase99_goal_outcome_evaluator_bundle

python ~/companyos/phase99_goal_outcome_evaluator_bundle/phase99_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase99_goal_outcome_evaluator_bundle/phase99_verify.py

TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase99_goal_outcome_test.py

EVALUATE A REAL GOAL:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase99_runtime_goal_evaluate.py "<GOAL_ID>"
