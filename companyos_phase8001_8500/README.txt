CompanyOS Phase 8001-8500
REAL PROVIDER EXECUTION ADAPTERS

This 500-phase push adds:
- provider adapter contracts + registry
- generic HTTP execution adapter
- safe local command execution adapter
- SMTP adapter
- research/deployment/finance-read adapters
- credential readiness checks
- request-signing policy references
- circuit breaker
- quota management
- provider execution engine
- receipt verification
- approval gating for consequential external actions
- persistent state + audit
- unified CEO provider execution controller

NOTE:
The included demo runs with live=False.
Real external calls require actual connector configuration and credentials.
Production deploys, external messages, transfers, contracts, etc. remain approval-gated.

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase8001_8500_real_provider_execution_adapters.zip .
unzip -o companyos_phase8001_8500_real_provider_execution_adapters.zip
bash companyos_phase8001_8500/install.sh ~/companyos

RUN:
bash ~/companyos/scripts/companyos_providerexec.sh status
bash ~/companyos/scripts/companyos_providerexec.sh verify
bash ~/companyos/scripts/companyos_providerexec.sh cycle
