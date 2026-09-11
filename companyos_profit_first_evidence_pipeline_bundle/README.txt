COMPANYOS PROFIT-FIRST EVIDENCE PIPELINE

Purpose:
Turn research artifacts into actual economic rankings instead of letting CompanyOS build from vague ideas.

What it does:
- Scans current CompanyOS JSON artifacts in workspace, exports, artifacts, and runtime.
- Finds opportunity/venture records that contain economic evidence.
- Normalizes economics into the Profit-First scoring model.
- Deduplicates repeated/renamed opportunities.
- Scores and ranks candidates.
- Selects at most the top 3 evidence-backed validation bets.
- Refuses to authorize a build when nothing clears the configured investment threshold.
- Writes:
  .companyos_runtime/profit_first_evidence_report.json

INSTALL

cd ~/companyos || exit 1
rm -rf companyos_profit_first_evidence_pipeline_bundle
mkdir -p companyos_profit_first_evidence_pipeline_bundle

unzip -o ~/storage/downloads/COMPANYOS_PROFIT_FIRST_EVIDENCE_PIPELINE_BUNDLE.zip   -d ~/companyos/companyos_profit_first_evidence_pipeline_bundle

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_profit_first_evidence_pipeline_bundle/install.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_profit_first_evidence_pipeline_bundle/verify.py

Run evidence ranking:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_profit_first_evidence.py
