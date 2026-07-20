COMPANYOS PHASE 285-292
PERSISTENT SELF-IMPROVEMENT RUNTIME

285 Durable improvement state store
286 Append-only persistent cycle journal
287 Pause/repeated-failure policy
288 Adaptive delay scheduler
289 Capability dedupe helper
290 Persistent improvement runner
291 Pause/resume/status controller
292 Persistent runtime/status

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase285_292_persistent_self_improvement.zip .
unzip -o companyos_phase285_292_persistent_self_improvement.zip
bash companyos_phase285_292_persistent_self_improvement/install.sh ~/companyos

EXPECTED:
phase285_292_verification_passed
phase292_persistent_self_improvement_ready
3 passed
PHASE285_292_INSTALL_OK
PERSISTENT_SELF_IMPROVEMENT=READY

CONTROL:
python ~/companyos/scripts/persistent_control.py status
python ~/companyos/scripts/persistent_control.py pause
python ~/companyos/scripts/persistent_control.py resume

LIVE RUN:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_persistent_improvement.py --rounds 1

For multi-round persistent runs:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_persistent_improvement.py --rounds 3 --sleep-between

A live run can use model credits.
