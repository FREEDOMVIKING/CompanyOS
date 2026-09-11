PHASE 89 — PRODUCTION RUNTIME SUPERVISOR

Adds one persistent runtime supervisor tying together:

Phase 88 boot readiness
-> live treasury refresh
-> Phase 87 reconciliation gate
-> persisted supervisor health state
-> repeated health cycles
-> max consecutive failure stop guard

The supervisor itself never builds, signs, or broadcasts transactions.
Financial execution remains delegated to the production execution coordinator.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase89_production_runtime_supervisor_bundle
mkdir -p phase89_production_runtime_supervisor_bundle

unzip -o ~/storage/downloads/PHASE89_PRODUCTION_RUNTIME_SUPERVISOR_BUNDLE.zip \
  -d ~/companyos/phase89_production_runtime_supervisor_bundle

python ~/companyos/phase89_production_runtime_supervisor_bundle/phase89_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase89_production_runtime_supervisor_bundle/phase89_verify.py

ONE-CYCLE TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase89_supervisor_once.py

CONTINUOUS SUPERVISOR:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase89_supervisor_run.py --interval 15 --max-failures 5

CTRL+C stops the continuous supervisor.
