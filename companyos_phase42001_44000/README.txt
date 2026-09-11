CompanyOS Phase 42001-44000
WALLET SIGNER END-TO-END VALIDATION

Purpose:
Validate the real signer boundary before enabling any live autonomous money movement.

Validation path:
CompanyOS
 -> treasury-gated wallet path
 -> existing signer command probe
 -> unsigned Solana intent creation
 -> signature-structure inspection
 -> Solana simulateTransaction when a serialized signed transaction is returned
 -> validation report
 -> NO BROADCAST

Important:
- This bundle does not enable live financial execution.
- It does not copy or print private-key material.
- It does not broadcast a transaction.
- ready_for_live remains false.
- The report may mark ready_for_live_review=true only if signer probe, signature evidence,
  and RPC simulation all pass.

INSTALL:
cd ~/companyos
cp /sdcard/Download/CompanyOS_SIGNER_VALIDATION_44000.zip .
unzip -o CompanyOS_SIGNER_VALIDATION_44000.zip
bash companyos_phase42001_44000/install.sh ~/companyos

THEN:
bash ~/companyos/scripts/companyos_signervalidation.sh validate
bash ~/companyos/scripts/companyos_signervalidation.sh report
bash ~/companyos/scripts/companyos_signervalidation.sh status
