CompanyOS Phase 6001-6500
PRODUCTION HARDENING + OBSERVABILITY

This 500-phase bundled push adds:
- unified component health matrix
- SLO evaluation
- incident classification
- backup manifests
- integrity checking
- runtime config validation
- plaintext-secret reference auditing
- rollback planning
- chaos/recovery probes
- capacity planning
- observability snapshots
- production release gating
- persistent hardening state
- hardening audit trail
- unified production hardening controller

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase6001_6500_production_hardening_observability.zip .
unzip -o companyos_phase6001_6500_production_hardening_observability.zip
bash companyos_phase6001_6500/install.sh ~/companyos

RUN:
bash ~/companyos/scripts/companyos_hardening.sh status
bash ~/companyos/scripts/companyos_hardening.sh cycle
bash ~/companyos/scripts/companyos_hardening.sh verify
