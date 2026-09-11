COMPANYOS ORCHESTRATION CANDIDATE EXTRACTOR V2

Purpose:
Fix the confirmed state:
research output exists but candidate_files_tied_to_orchestration = 0

V2 specifically:
- uses the exact traced opportunity-expansion orchestration ID
- scans matching journal records and artifact files
- extracts nested JSON candidate objects
- extracts candidate-like opportunity blocks embedded in prose/text output
- normalizes them into Profit-First candidate JSON
- stamps/repairst exact orchestration lineage
- preserves richer existing evidence when repairing lineage
- does not seed fake opportunities

INSTALL

cd ~/companyos || exit 1

rm -rf companyos_orchestration_candidate_extractor_v2_bundle
mkdir -p companyos_orchestration_candidate_extractor_v2_bundle

unzip -o ~/storage/downloads/COMPANYOS_ORCHESTRATION_CANDIDATE_EXTRACTOR_V2_BUNDLE.zip   -d ~/companyos/companyos_orchestration_candidate_extractor_v2_bundle

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_orchestration_candidate_extractor_v2_bundle/install.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_orchestration_candidate_extractor_v2_bundle/verify.py

Run extraction + ranking:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_extract_then_rank_profit_first.py

Then inspect exact lineage:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_trace_profit_first_orchestration.py
