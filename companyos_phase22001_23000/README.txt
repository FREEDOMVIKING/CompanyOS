CompanyOS Phase 22001-23000
POLICY-ENFORCED FINANCIAL EXECUTION FRAMEWORK

This phase connects the Phase 22000 treasury safety kernel to a formal payment execution layer.

Included:
- payment connector interface
- connector registry
- sandbox connector
- policy-enforced payment orchestration
- approval queue
- idempotency keys
- treasury ledger recording
- reconciliation

Important:
This bundle DOES NOT connect a real bank, card, crypto wallet, or payment account.
REAL_PROVIDER_CONNECTED=FALSE
REAL_MONEY_ENABLED=FALSE

That is intentional.

The next step is to choose ONE real provider and build a dedicated connector around its
official API while keeping the existing:
- allowlist
- per-transaction limit
- daily spend ceiling
- reserve floor
- loss limit
- ledger
- reconciliation
- approval fallback

INSTALL:
cd ~/companyos
cp /sdcard/Download/CompanyOS_FINANCIAL_EXECUTION_23000.zip .
unzip -o CompanyOS_FINANCIAL_EXECUTION_23000.zip
bash companyos_phase22001_23000/install.sh ~/companyos

VERIFY:
bash ~/companyos/scripts/companyos_payments.sh verify

SANDBOX DEMO:
bash ~/companyos/scripts/companyos_payments.sh demo

STATUS:
bash ~/companyos/scripts/companyos_payments.sh status
