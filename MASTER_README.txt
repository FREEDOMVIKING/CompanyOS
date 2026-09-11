COMPANYOS MASTER FINAL BUILD
Consolidated through Phase 16000

This master package contains the uploaded full CompanyOS codebase plus the final durable worker execution and queue-drain layer.

Key final runtime path:
1. CI/CD validates/builds/releases.
2. Daemon stays alive and creates/routes durable work.
3. Durable workers claim/lease/execute jobs.
4. Completed jobs are deduplicated.
5. Failed jobs retry or dead-letter.
6. Backpressure protects the queue.
7. Restart recovery resumes unfinished work.
8. Existing governance/approval boundaries remain in force for consequential external actions.

INSTALL/UPGRADE:
cd /path/to/extracted/CompanyOS_MASTER_FINAL
bash install_master.sh ~/companyos

VERIFY:
bash ~/companyos/scripts/companyos_master_verify.sh

DRAIN CURRENT QUEUE:
bash ~/companyos/scripts/companyos_worker.sh drain

START CONTINUOUS RUNTIME:
bash ~/companyos/scripts/companyos_daemon_control.sh start

CHECK:
bash ~/companyos/scripts/companyos_daemon_control.sh status
bash ~/companyos/scripts/companyos_daemon_control.sh logs


PHASE 16500 ADDITION:
Real capability execution layer with provider endpoints, persistent execution receipts, runtime memory bridge, and approval-preserving external execution routing.
