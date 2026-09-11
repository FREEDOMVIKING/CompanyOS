CompanyOS Phase 24001-25000
TREASURY-GATED MULTICHAIN EXECUTION

This phase bridges the existing live:
  ~/companyos/agents/multichain_execution_adapter.py

into the treasury/payment framework already built in Phases 22000-24000.

Architecture:
Autonomous CEO
  -> treasury policy
  -> destination allowlist
  -> transaction/day/reserve/loss limits
  -> financial kill switch
  -> idempotency
  -> existing multichain adapter
  -> isolated signer command
  -> blockchain
  -> receipt + treasury ledger

Supported routes are inherited from the existing adapter:
- Solana
- EVM
- Bitcoin

Safety:
- Live execution is OFF by default.
- Dry-run authorization is the default behavior.
- The existing signing_authorized gate remains required.
- COMPANYOS_ENABLE_LIVE_FINANCIAL_EXECUTION must be explicitly enabled for live execution.
- No private keys are embedded or copied into this package.
- Every request passes treasury policy first.
- A financial kill switch can immediately stop new execution.

INSTALL:
cd ~/companyos
cp /sdcard/Download/CompanyOS_TREASURY_MULTICHAIN_25000.zip .
unzip -o CompanyOS_TREASURY_MULTICHAIN_25000.zip
bash companyos_phase24001_25000/install.sh ~/companyos

CHECK READINESS:
bash ~/companyos/scripts/companyos_money.sh readiness

STATUS:
bash ~/companyos/scripts/companyos_money.sh status

EMERGENCY KILL:
bash ~/companyos/scripts/companyos_money.sh kill

CLEAR KILL:
bash ~/companyos/scripts/companyos_money.sh unkill

Do not enable live execution until readiness shows the intended RPCs and signer configuration.
