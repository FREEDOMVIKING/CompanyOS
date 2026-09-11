COMPANYOS CANDIDATE MATERIALIZATION + RESEARCH BRIDGE

Purpose:
Fix the state where market-scan orchestrations complete but:
  candidate_count = 0
  .companyos_runtime/profit_first_candidates/ is empty

This bundle does NOT seed fake opportunities.

It:
1. Reads real orchestration journals and JSON research/artifact outputs.
2. Extracts candidate-like opportunity records.
3. Normalizes them into the Profit-First candidate schema.
4. Writes structured JSON files to:
   .companyos_runtime/profit_first_candidates/
5. Marks weak/defaulted fields as estimates and lowers evidence confidence.
6. Deduplicates candidates by identity fingerprint.
7. If completed market scans still produce zero usable candidates, dispatches a targeted
   research-output recovery orchestration instead of silently counting success.

INSTALL

cd ~/companyos || exit 1

rm -rf companyos_candidate_materialization_research_bridge_bundle
mkdir -p companyos_candidate_materialization_research_bridge_bundle

unzip -o ~/storage/downloads/COMPANYOS_CANDIDATE_MATERIALIZATION_RESEARCH_BRIDGE_BUNDLE.zip   -d ~/companyos/companyos_candidate_materialization_research_bridge_bundle

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_candidate_materialization_research_bridge_bundle/install.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_candidate_materialization_research_bridge_bundle/verify.py

Run one immediate bridge pass:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_candidate_materialization.py

Restart autonomy:

bash scripts/companyos_productive_autonomy.sh restart

Wait 30-60 seconds, then:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_candidate_materialization_status.py

Then rerun evidence scoring:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_profit_first_evidence.py

Watch Activity Ledger:
http://127.0.0.1:8768

Look for:
PROFIT_FIRST_CANDIDATES_MATERIALIZED
PROFIT_FIRST_CANDIDATE_RECOVERY
