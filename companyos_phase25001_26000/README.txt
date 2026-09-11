CompanyOS Phase 25001-26000
AUTONOMOUS FINANCIAL OPERATIONS + END-TO-END SAFETY VALIDATION

Purpose:
Validate the complete financial control path before any autonomous live-money activation.

Path validated:
Financial intent
 -> treasury policy
 -> allowlist
 -> limits/reserve/loss checks
 -> kill switch
 -> idempotency
 -> multichain bridge
 -> signer boundary
 -> dry-run resolution
 -> safety validation
 -> activation eligibility report

This phase DOES NOT automatically enable real-money execution.

Live execution remains controlled by:
  COMPANYOS_ENABLE_LIVE_FINANCIAL_EXECUTION

The activation gate only reports whether the system is technically eligible for a later,
explicit live activation. It never flips the live switch itself.

INSTALL:
cd ~/companyos
cp /sdcard/Download/CompanyOS_FINANCIAL_VALIDATION_26000.zip .
unzip -o CompanyOS_FINANCIAL_VALIDATION_26000.zip
bash companyos_phase25001_26000/install.sh ~/companyos

VERIFY:
bash ~/companyos/scripts/companyos_finops.sh verify

STATUS:
bash ~/companyos/scripts/companyos_finops.sh status

READINESS:
bash ~/companyos/scripts/companyos_money.sh readiness

END-TO-END DRY RUN:
Use an address already in:
  ~/.companyos_runtime/crypto_destination_allowlist.json
through:
  python ~/companyos/scripts/companyos_financial_e2e.py ...
