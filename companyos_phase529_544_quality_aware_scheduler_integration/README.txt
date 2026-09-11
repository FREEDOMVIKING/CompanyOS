COMPANYOS PHASE 529-544
QUALITY-AWARE SCHEDULER INTEGRATION

529 candidate store
530 candidate router
531 targeted research-more mission
532 validation candidate builder
533 quality-to-scheduler bridge
534 quality mission generator
535 candidate priority
536 candidate deduper
537 candidate lifecycle state
538 scheduler quality hook
539 decision event router
540 quality portfolio memory
541 autonomous quality cycle
542 CEO quality scheduler
543 integration health
544 runtime/status

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase529_544_quality_aware_scheduler_integration.zip .
unzip -o companyos_phase529_544_quality_aware_scheduler_integration.zip
bash companyos_phase529_544_quality_aware_scheduler_integration/install.sh ~/companyos

EXPECTED:
phase529_544_verification_passed
phase544_quality_aware_scheduler_integration_ready
3 passed
PHASE529_544_INSTALL_OK
QUALITY_AWARE_SCHEDULER=READY

RUN:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_quality_scheduler_cycle.py
