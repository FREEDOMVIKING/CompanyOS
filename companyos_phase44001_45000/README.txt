CompanyOS Phase 44001-45000
SIGNER COMPATIBILITY BRIDGE

Purpose:
Diagnose and bridge the mismatch between CompanyOS's new validation layer
and the existing MULTICHAIN_SIGNER_COMMAND contract.

Adds:
- signer contract detection
- multiple safe JSON-stdin compatibility probes
- sanitized diagnostics
- compatible request selection
- compatibility report

Safety:
- No private-key material is printed.
- Signed transaction payload fields are redacted from diagnostics.
- No blockchain broadcast is attempted.
- Live execution remains disabled.

INSTALL:
cd ~/companyos
cp /sdcard/Download/CompanyOS_SIGNER_COMPAT_BRIDGE_45000.zip .
unzip -o CompanyOS_SIGNER_COMPAT_BRIDGE_45000.zip
bash companyos_phase44001_45000/install.sh ~/companyos

THEN:
bash ~/companyos/scripts/companyos_signercompat.sh probe
bash ~/companyos/scripts/companyos_signercompat.sh report
bash ~/companyos/scripts/companyos_signercompat.sh status
