PHASE 76 — LIVE TREASURY AUTHORIZATION

Adds a forced-fresh authorization layer for SOL financial decisions.

Behavior:
- refreshes the live wallet balance before authorization
- rejects stale/unavailable treasury state
- respects COMPANYOS_LIVE_MIN_RESERVE
- calculates spendable balance from current live balance
- does not rely on a hard-coded wallet balance

This phase does NOT create, sign, or broadcast transactions.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase76_live_treasury_authorization_bundle
mkdir -p phase76_live_treasury_authorization_bundle

unzip -o ~/storage/downloads/PHASE76_LIVE_TREASURY_AUTHORIZATION_BUNDLE.zip \
  -d ~/companyos/phase76_live_treasury_authorization_bundle

python ~/companyos/phase76_live_treasury_authorization_bundle/phase76_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase76_live_treasury_authorization_bundle/phase76_verify.py

RUN ZERO-VALUE AUTHORIZATION TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase76_live_treasury_auth_test.py
