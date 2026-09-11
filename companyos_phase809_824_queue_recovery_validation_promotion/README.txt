COMPANYOS PHASE 809-824
AUTONOMOUS QUEUE RECOVERY + VALIDATION PROMOTION

Purpose:
- recover deferred research through alternate providers
- merge evidence
- promote qualified research to validation
- retire stale integration-test missions
- deduplicate queue entries
- prevent retry loops
- prove the queue drains instead of growing

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase809_824_queue_recovery_validation_promotion.zip .
unzip -o companyos_phase809_824_queue_recovery_validation_promotion.zip
bash companyos_phase809_824_queue_recovery_validation_promotion/install.sh ~/companyos

EXPECTED:
phase809_824_verification_passed
phase824_queue_recovery_validation_promotion_ready
3 passed
PHASE809_824_INSTALL_OK

RUN STATUS:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/queue_recovery_status.py

RUN ONE RECOVERY CYCLE:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_queue_recovery.py --max-recoveries 3

THEN CHECK STATUS AGAIN:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/queue_recovery_status.py
