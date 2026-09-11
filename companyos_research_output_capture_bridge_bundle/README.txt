COMPANYOS RESEARCH OUTPUT CAPTURE BRIDGE

Purpose:
Fix the confirmed root bottleneck:
CompanyOS reports research output exists, but no machine-readable candidate payload is persisted.

This bundle instruments the AutonomousCEOOrchestrator boundary itself.

How it works:
- Wraps AutonomousCEOOrchestrator.start()
- Uses Python profiling during each orchestration to capture return values from CompanyOS
  research/discovery/opportunity/market/venture/agent/evaluation functions
- Persists raw captured payloads to:
  .companyos_runtime/canonical_research_outputs/
- Preserves orchestration lineage when available
- Provides a post-capture extractor that converts real captured opportunities into
  Profit-First candidate JSON using the existing V2 extractor logic
- Does not seed fake candidates

INSTALL

cd ~/companyos || exit 1

rm -rf companyos_research_output_capture_bridge_bundle
mkdir -p companyos_research_output_capture_bridge_bundle

unzip -o ~/storage/downloads/COMPANYOS_RESEARCH_OUTPUT_CAPTURE_BRIDGE_BUNDLE.zip   -d ~/companyos/companyos_research_output_capture_bridge_bundle

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_research_output_capture_bridge_bundle/install.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_research_output_capture_bridge_bundle/verify.py

Restart autonomy so future orchestrations are captured:

bash scripts/companyos_productive_autonomy.sh restart

Trigger one profit-first stage:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_profit_first_enrichment_expansion_once.py

Wait 30-60 seconds, then inspect capture:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_research_output_capture_status.py

Extract captured opportunities:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_extract_canonical_research_outputs.py

Then rank:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_profit_first_evidence.py
