COMPANYOS RESEARCH OUTPUT -> CANDIDATE MATERIALIZER V2

Purpose:
Repair the confirmed state:
research_output_exists_but_not_materialized

This V2 materializer reads the canonical research capture files directly and extracts opportunity candidates from:
- nested JSON structures
- JSON blobs embedded in strings
- markdown/prose candidate sections
- captured goal/result/return envelopes

It then:
- normalizes candidate schema
- preserves low confidence for weak/prose-only evidence
- repairs orchestration lineage
- writes structured candidate JSON files
- runs cleanly with the existing Profit-First Evidence Pipeline

No fake candidates are seeded.
No thresholds are lowered.

INSTALL

cd ~/companyos || exit 1

rm -rf companyos_research_output_candidate_materializer_v2_bundle
mkdir -p companyos_research_output_candidate_materializer_v2_bundle

unzip -o ~/storage/downloads/COMPANYOS_RESEARCH_OUTPUT_CANDIDATE_MATERIALIZER_V2_BUNDLE.zip   -d ~/companyos/companyos_research_output_candidate_materializer_v2_bundle

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_research_output_candidate_materializer_v2_bundle/install.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_research_output_candidate_materializer_v2_bundle/verify.py

Run materialization + ranking:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_materialize_v2_then_rank.py

Then inspect:
find .companyos_runtime/profit_first_candidates -maxdepth 1 -type f | wc -l

And rerun:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_profit_first_evidence.py
