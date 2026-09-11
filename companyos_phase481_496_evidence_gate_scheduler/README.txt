COMPANYOS PHASE 481-496
EVIDENCE GATES + PERSISTENT CEO MISSION SCHEDULER

481 mission state
482 durable mission queue
483 evidence gate
484 validation metrics store
485 operations metrics store
486 gate resolver
487 mission scheduler
488 research mission
489 validation mission
490 venture mission
491 build mission
492 operations mission
493 portfolio mission
494 mission orchestrator
495 persistent mission scheduler
496 runtime/status

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase481_496_evidence_gate_scheduler.zip .
unzip -o companyos_phase481_496_evidence_gate_scheduler.zip
bash companyos_phase481_496_evidence_gate_scheduler/install.sh ~/companyos

EXPECTED:
phase481_496_verification_passed
phase496_evidence_gate_scheduler_ready
3 passed
PHASE481_496_INSTALL_OK
EVIDENCE_GATE_SCHEDULER=READY
PERSISTENT_MISSION_QUEUE=READY

This phase gives the persistent CEO a real mission queue and explicit evidence stores,
so validation and operations stages can resume later when metrics arrive instead of
losing state or requiring a full manual restart.
