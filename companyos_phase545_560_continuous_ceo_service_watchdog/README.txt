COMPANYOS PHASE 545-560
CONTINUOUS CEO SERVICE + WATCHDOG

545 service configuration
546 persistent service state
547 quality-aware tick
548 autonomous scheduler tick
549 coordinated tick runner
550 idle policy
551 failure backoff
552 duplicate-instance lock
553 service journal
554 crash recovery
555 health snapshot
556 watchdog
557 startup recovery
558 continuous service loop
559 one-command autonomous CEO service
560 runtime/status

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase545_560_continuous_ceo_service_watchdog.zip .
unzip -o companyos_phase545_560_continuous_ceo_service_watchdog.zip
bash companyos_phase545_560_continuous_ceo_service_watchdog/install.sh ~/companyos

EXPECTED:
phase545_560_verification_passed
phase560_continuous_ceo_service_watchdog_ready
3 passed
PHASE545_560_INSTALL_OK
CONTINUOUS_CEO_SERVICE=READY
WATCHDOG=READY

SAFE ONE-TICK TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_ceo_service.py --max-ticks 1

BACKGROUND START:
bash ~/companyos/scripts/start_ceo_service.sh

HEALTH:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/ceo_service_health.py

STOP:
bash ~/companyos/scripts/stop_ceo_service.sh

Note: Android battery optimization can pause Termux background processes.
This bundle adds service persistence/recovery logic, but OS-level uptime still depends on Termux staying alive.
