COMPANYOS PHASE 93-100 LARGE PUSH

93 Mission lifecycle board
94 Autonomous internal task queue
95 Artifact registry and lineage
96 Central approval center
97 Production-readiness gate
98 External action router
99 Audit trail
100 Production CEO orchestration layer

This bundle is additive and does not overwrite the CompanyOS core.

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase93_100_large_push.zip .
unzip -o companyos_phase93_100_large_push.zip
bash companyos_phase93_100_large_push/install.sh ~/companyos

EXPECTED:
"status": "phase93_100_verification_passed"
"cycle_status": "phase100_production_ceo_cycle_completed"
PHASE93_100_INSTALL_OK
