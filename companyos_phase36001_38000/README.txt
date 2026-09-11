CompanyOS Phase 36001-38000
INTEGRATED AUTONOMOUS RUNTIME

This phase takes the real execution cycle and places it inside a persistent runtime.

Adds:
- repeated real-capability operating cycles
- durable checkpoints
- runtime health snapshots
- automatic recovery classification
- pause/resume behavior for approval gates
- missing-capability detection
- false-completion prevention
- start/stop/restart/status/log controls

Important:
This still does not automatically enable live money movement.
Treasury and live financial controls remain separate.

INSTALL:
cd ~/companyos
cp /sdcard/Download/CompanyOS_AUTONOMOUS_RUNTIME_38000.zip .
unzip -o CompanyOS_AUTONOMOUS_RUNTIME_38000.zip
bash companyos_phase36001_38000/install.sh ~/companyos

TEST ONE FULL INTEGRATED CYCLE:
bash ~/companyos/scripts/companyos_runtime_integration.sh once

START PERSISTENT RUNTIME:
bash ~/companyos/scripts/companyos_runtime_integration.sh start

STATUS:
bash ~/companyos/scripts/companyos_runtime_integration.sh status

LOGS:
bash ~/companyos/scripts/companyos_runtime_integration.sh logs
