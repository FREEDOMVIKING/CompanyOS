CompanyOS Phase 30001-32000
REAL CAPABILITY WIRING + CONTROLLED AUTONOMY

This phase starts connecting the Phase 30000 operating lifecycle to real CompanyOS capability names.

Adds:
- stage-to-capability routing
- controlled autonomy policy
- real-capability execution planning
- automatic permission for bounded reversible actions
- approval gates for irreversible/high-impact production actions
- treasury policy preservation
- credential-change protection

This phase intentionally does not assume a capability exists just because a lifecycle stage exists.
Use:
  bash ~/companyos/scripts/companyos_capabilityops.sh scan
to see what capabilities are actually present in the live installation.

Install:
cd ~/companyos
cp /sdcard/Download/CompanyOS_REAL_CAPABILITY_WIRING_32000.zip .
unzip -o CompanyOS_REAL_CAPABILITY_WIRING_32000.zip
bash companyos_phase30001_32000/install.sh ~/companyos
