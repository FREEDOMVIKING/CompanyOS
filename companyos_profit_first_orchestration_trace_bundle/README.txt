COMPANYOS PROFIT-FIRST ORCHESTRATION TRACE + REPAIR

Purpose:
Trace the exact latest opportunity-expansion orchestration end-to-end and determine whether:
1. research output exists in journals/artifacts,
2. output was materialized into candidate JSON,
3. the evidence engine sees the resulting candidates.

This avoids guessing and avoids installing another large behavior patch before locating the real bottleneck.

INSTALL

cd ~/companyos || exit 1

rm -rf companyos_profit_first_orchestration_trace_bundle
mkdir -p companyos_profit_first_orchestration_trace_bundle

unzip -o ~/storage/downloads/COMPANYOS_PROFIT_FIRST_ORCHESTRATION_TRACE_BUNDLE.zip   -d ~/companyos/companyos_profit_first_orchestration_trace_bundle

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_profit_first_orchestration_trace_bundle/install.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_profit_first_orchestration_trace_bundle/verify.py

Run exact trace:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_trace_profit_first_orchestration.py

Run trace + automatic safe repair:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_profit_first_trace_and_repair.py

Then rerun evidence:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_profit_first_evidence.py

Report:
.companyos_runtime/profit_first_orchestration_trace_report.json
