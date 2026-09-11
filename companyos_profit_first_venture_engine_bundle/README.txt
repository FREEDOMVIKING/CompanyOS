COMPANYOS PROFIT-FIRST AUTONOMOUS VENTURE ENGINE

Purpose:
Make CompanyOS optimize for sustainable long-term risk-adjusted economic value,
not construction, services, number of companies, or ease of generating artifacts.

Key changes:
- Business-model-neutral discovery.
- 20+ candidates, 8+ unrelated sectors, 7+ business-model families.
- Profit/economic evidence scoring.
- Research-before-build.
- No forced venture creation below investment threshold.
- Maximum 3 simultaneous new validation bets.
- Portfolio compare/kill/improve/reallocate/scale logic in the CEO directive.
- Existing external approval, financial, signer, reconciliation, and irreversible-action gates remain intact.
- Integrates with diversified discovery and idle-cycle recovery.

INSTALL

cd ~/companyos || exit 1
rm -rf companyos_profit_first_venture_engine_bundle
mkdir -p companyos_profit_first_venture_engine_bundle

unzip -o ~/storage/downloads/COMPANYOS_PROFIT_FIRST_VENTURE_ENGINE_BUNDLE.zip   -d ~/companyos/companyos_profit_first_venture_engine_bundle

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_profit_first_venture_engine_bundle/install.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_profit_first_venture_engine_bundle/verify.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_profit_first_status.py

bash scripts/companyos_productive_autonomy.sh restart

This bundle does NOT bypass spending, wallet, signer, external-action, approval,
reconciliation, legal, destructive, or irreversible-action controls.
