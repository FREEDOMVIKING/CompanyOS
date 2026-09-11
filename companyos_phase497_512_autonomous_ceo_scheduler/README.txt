COMPANYOS PHASE 497-512
AUTONOMOUS CEO MISSION GENERATION + SCHEDULER

497 objective store
498 automatic mission generator
499 dependency resolver
500 event store
501 event router
502 mission deduper
503 mission budget
504 dynamic reprioritizer
505 scheduler heartbeat
506 stalled-work detector
507 resume engine
508 scheduler state
509 mission audit
510 autonomous CEO scheduler tick
511 scheduler bridge
512 runtime/status

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase497_512_autonomous_ceo_scheduler.zip .
unzip -o companyos_phase497_512_autonomous_ceo_scheduler.zip
bash companyos_phase497_512_autonomous_ceo_scheduler/install.sh ~/companyos

EXPECTED:
phase497_512_verification_passed
phase512_autonomous_ceo_scheduler_ready
3 passed
PHASE497_512_INSTALL_OK
AUTONOMOUS_CEO_SCHEDULER=READY

FIRST SCHEDULER TICK:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_ceo_scheduler_tick.py
