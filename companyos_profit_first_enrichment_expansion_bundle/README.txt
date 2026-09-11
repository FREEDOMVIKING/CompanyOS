COMPANYOS PROFIT-FIRST ENRICHMENT + OPPORTUNITY EXPANSION

Purpose:
Move CompanyOS from:
2 candidates / 2 sectors / 1 business model / 0 qualified
toward a diversified, evidence-backed opportunity portfolio.

Autonomous stages:
1. OPPORTUNITY EXPANSION
   - target 20+ materially different candidates
   - target 8+ unrelated sectors
   - target 7+ business-model families
   - explicitly rejects superficial construction/SMB-AI variants

2. EVIDENCE ENRICHMENT
   - strengthens economics, demand, competition, CAC, risk, moat, margins, ROI
   - separates facts, estimates, assumptions, unknowns
   - does NOT inflate confidence to force qualification

3. VALIDATION QUEUE
   - once candidates qualify, creates internal/reversible validation plans
   - max top 3 validation bets
   - still does not auto-build without sufficient evidence

No thresholds are lowered.
No fake candidates are seeded.
Existing external-action, spending, financial, credential, signer, reconciliation,
publication/deployment, legal, destructive, and irreversible-action gates remain intact.

INSTALL

cd ~/companyos || exit 1

rm -rf companyos_profit_first_enrichment_expansion_bundle
mkdir -p companyos_profit_first_enrichment_expansion_bundle

unzip -o ~/storage/downloads/COMPANYOS_PROFIT_FIRST_ENRICHMENT_EXPANSION_BUNDLE.zip   -d ~/companyos/companyos_profit_first_enrichment_expansion_bundle

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_profit_first_enrichment_expansion_bundle/install.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_profit_first_enrichment_expansion_bundle/verify.py

Run one stage immediately:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_profit_first_enrichment_expansion_once.py

Restart:

bash scripts/companyos_productive_autonomy.sh restart

After 30-60 seconds:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_candidate_materialization.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_profit_first_evidence.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_profit_first_enrichment_expansion_status.py

Watch:
http://127.0.0.1:8768

Look for:
PROFIT_FIRST_ENRICHMENT_EXPANSION
