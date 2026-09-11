PHASE 96 — CEO GOAL -> TASK DECOMPOSITION

Builds on Phase 94 + 95.

Adds:
- high-level CEO goal submission
- deterministic decomposition into:
  research -> planning -> build
- dependency-aware dispatch
- idempotent per-goal task keys
- durable queue persistence

Phase 96 itself never signs or broadcasts transactions.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase96_ceo_goal_decomposition_bundle
mkdir -p phase96_ceo_goal_decomposition_bundle

unzip -o ~/storage/downloads/PHASE96_CEO_GOAL_DECOMPOSITION_BUNDLE.zip \
  -d ~/companyos/phase96_ceo_goal_decomposition_bundle

python ~/companyos/phase96_ceo_goal_decomposition_bundle/phase96_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase96_ceo_goal_decomposition_bundle/phase96_verify.py

TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase96_goal_decomposition_test.py

SUBMIT A REAL INTERNAL GOAL:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase96_runtime_goal_submit.py "research and plan a small digital product idea"
