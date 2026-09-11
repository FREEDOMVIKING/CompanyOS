PHASE 108 — RESEARCH SIGNAL INGESTION + NORMALIZATION

Builds on Phase 106 + 107.

FLOW:
raw research/news/market/product signal
 -> persistent signal store
 -> deduplication
 -> deterministic normalization
 -> Phase 107 evidence record
 -> research assessment
 -> opportunity score update

This creates the connector-ready boundary for future live research sources.

IMPORTANT:
Phase 108 does NOT fetch the web by itself.
It accepts signals from future connectors, agents, APIs, or manual imports.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase108_research_signal_ingestion_bundle
mkdir -p phase108_research_signal_ingestion_bundle

unzip -o ~/storage/downloads/PHASE108_RESEARCH_SIGNAL_INGESTION_BUNDLE.zip \
  -d ~/companyos/phase108_research_signal_ingestion_bundle

python ~/companyos/phase108_research_signal_ingestion_bundle/phase108_install.py

VERIFY:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase108_research_signal_ingestion_bundle/phase108_verify.py

TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase108_signal_pipeline_test.py
