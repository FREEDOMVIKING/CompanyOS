CompanyOS Phase 40001-42000
EXISTING WALLET AUTOBIND + SOLANA PREFLIGHT

Purpose:
Fix the missing crypto_wallet_binding.json state without creating a second wallet
or copying private-key material.

Adds:
- existing wallet autodiscovery
- binding metadata generation
- Solana RPC health check
- latest-blockhash preflight check
- signer-presence validation without exposing signer command values
- dry-run readiness state generation

Important:
This phase DOES NOT sign or broadcast a transaction.
It intentionally leaves:
  ready_for_live = false
  live_execution_auto_enabled = false

INSTALL:
cd ~/companyos
cp /sdcard/Download/CompanyOS_WALLET_AUTOBIND_PREFLIGHT_42000.zip .
unzip -o CompanyOS_WALLET_AUTOBIND_PREFLIGHT_42000.zip
bash companyos_phase40001_42000/install.sh ~/companyos

THEN:
bash ~/companyos/scripts/companyos_wallet_autobind.sh scan
bash ~/companyos/scripts/companyos_wallet_autobind.sh bind
bash ~/companyos/scripts/companyos_wallet_autobind.sh preflight
bash ~/companyos/scripts/companyos_wallet_execution.sh readiness
