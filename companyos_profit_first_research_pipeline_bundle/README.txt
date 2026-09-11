COMPANYOS PROFIT-FIRST RESEARCH PIPELINE

Purpose:
Fix candidate_count=0 by making the autonomous CEO create structured, evidence-bearing
opportunity records that the Profit-First Evidence Pipeline can actually score.

Pipeline:
1. MARKET SCAN
   - 20+ materially different opportunities
   - 8+ unrelated sectors
   - 7+ business-model families
   - structured JSON candidate records

2. EVIDENCE ENRICHMENT
   - improve demand/economics/competition/CAC/risk evidence
   - distinguish facts, estimates, assumptions, unknowns
   - conservative evidence confidence

3. EXISTING EVIDENCE PIPELINE
   - scores/ranks candidates
   - selects max top 3 validation bets
   - refuses weak builds below threshold

Candidate files are stored under:
.companyos_runtime/profit_first_candidates/

INSTALL

cd ~/companyos || exit 1
rm -rf companyos_profit_first_research_pipeline_bundle
mkdir -p companyos_profit_first_research_pipeline_bundle

unzip -o ~/storage/downloads/COMPANYOS_PROFIT_FIRST_RESEARCH_PIPELINE_BUNDLE.zip   -d ~/companyos/companyos_profit_first_research_pipeline_bundle

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_profit_first_research_pipeline_bundle/install.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_profit_first_research_pipeline_bundle/verify.py

bash scripts/companyos_productive_autonomy.sh restart

Wait 30-60 seconds, then:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_profit_first_research_status.py

Then rerun evidence ranking:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_profit_first_evidence.py

Watch Activity Ledger:
http://127.0.0.1:8768

Look for:
PROFIT_FIRST_RESEARCH
