CompanyOS Phase 38001-40000
WALLET EXECUTION WIRING + TREASURY CONTROL

Purpose:
Reuse the existing CompanyOS multichain wallet/execution code and place Solana execution
behind mandatory treasury, idempotency, preflight, kill-switch, and receipt-verification gates.

Architecture:
CompanyOS decision
 -> treasury authorization
 -> destination allowlist
 -> single/daily/reserve/loss limits
 -> kill switch
 -> idempotency
 -> existing multichain Solana route
 -> existing isolated signer
 -> preflight
 -> optional broadcast only when explicitly live-enabled and signing-authorized
 -> on-chain receipt verification
 -> treasury ledger/accounting

Safety:
- No new wallet is created.
- No private keys are embedded or copied.
- Signer command is reused; its value is not printed by readiness.
- Live execution remains OFF by default.
- A successful live execution is not accepted without transaction evidence.

INSTALL:
cd ~/companyos
cp /sdcard/Download/CompanyOS_WALLET_EXECUTION_WIRING_40000.zip .
unzip -o CompanyOS_WALLET_EXECUTION_WIRING_40000.zip
bash companyos_phase38001_40000/install.sh ~/companyos

THEN:
bash ~/companyos/scripts/companyos_wallet_execution.sh readiness
bash ~/companyos/scripts/companyos_wallet_execution.sh status
