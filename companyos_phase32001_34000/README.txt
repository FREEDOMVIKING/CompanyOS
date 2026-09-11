CompanyOS Phase 32001-34000
REAL CAPABILITY EXECUTION + VERIFIED RECEIPTS

This phase moves CompanyOS from lifecycle routing toward actual module execution.

Adds:
- dynamic discovery of real capability modules
- fallback discovery for missing routes such as release/deployment/marketing
- safe dynamic execution adapter
- execution receipts
- post-execution verification
- false-completion prevention

A stage is not considered successfully executed merely because a function returned.
The verifier requires both:
1. success=True
2. evidence such as output, receipt, artifact, path, tx_id, or completed/executed status.

Preview commands do not trigger external side effects.

INSTALL:
cd ~/companyos
cp /sdcard/Download/CompanyOS_REAL_EXECUTION_RECEIPTS_34000.zip .
unzip -o CompanyOS_REAL_EXECUTION_RECEIPTS_34000.zip
bash companyos_phase32001_34000/install.sh ~/companyos
