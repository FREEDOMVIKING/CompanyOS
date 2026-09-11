COMPANYOS PROFIT-FIRST DISPATCHER INTEGRATION

Purpose:
Connect the installed Profit-First Venture Engine to the live watchdog so healthy-but-idle CompanyOS
automatically starts profit-first opportunity discovery and validation work.

Behavior:
- Detects active=0, dispatched=0, last_orchestration_id=null.
- After 20 idle cycles, dispatches a profit-first orchestration.
- 5-minute cooldown prevents spam.
- Requires ranked evidence and concrete internal/reversible work.
- Maximum top 3 validation bets.
- If nothing clears the investment threshold, continue research instead of forcing a build.
- Preserves existing external-action, spending, financial, wallet/signer, reconciliation,
  publication/deployment, legal, destructive, and irreversible-action gates.

INSTALL

cd ~/companyos || exit 1

rm -rf companyos_profit_first_dispatcher_integration_bundle
mkdir -p companyos_profit_first_dispatcher_integration_bundle

unzip -o ~/storage/downloads/COMPANYOS_PROFIT_FIRST_DISPATCHER_INTEGRATION_BUNDLE.zip   -d ~/companyos/companyos_profit_first_dispatcher_integration_bundle

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_profit_first_dispatcher_integration_bundle/install.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_profit_first_dispatcher_integration_bundle/verify.py

bash scripts/companyos_productive_autonomy.sh restart

sleep 20

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_profit_first_dispatcher_status.py

Watch:
http://127.0.0.1:8768

Look for:
PROFIT_FIRST_DISPATCH
