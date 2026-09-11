COMPANYOS PHASE 465-480
PERSISTENT CEO OPERATING LOOP

465 unified stage contract
466 persistent CEO state
467 stage router
468 bounded cycle budget
469 decision journal
470 opportunity stage
471 validation stage
472 venture stage
473 build stage
474 operations stage
475 portfolio stage
476 failure recovery
477 system bridge
478 bounded CEO cycle
479 persistent CEO runner
480 runtime/status

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase465_480_persistent_ceo_operating_loop.zip .
unzip -o companyos_phase465_480_persistent_ceo_operating_loop.zip
bash companyos_phase465_480_persistent_ceo_operating_loop/install.sh ~/companyos

EXPECTED:
phase465_480_verification_passed
phase480_persistent_ceo_operating_loop_ready
3 passed
PHASE465_480_INSTALL_OK
PERSISTENT_CEO_OPERATING_LOOP=READY

FIRST SAFE RUN:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_persistent_ceo.py --cycles 1

This unifies the previously separate subsystems under one persistent CEO state machine.
Validation evidence and operating metrics are still required before the loop advances
through those evidence-dependent gates.
