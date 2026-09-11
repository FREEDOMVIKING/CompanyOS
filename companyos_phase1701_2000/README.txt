CompanyOS Phase 1701-2000
PERSISTENT AUTONOMOUS COMPANY RUNTIME

This 300-phase bundled push adds:
- persistent job queue
- heartbeat/watchdog
- autonomous cadence scheduler
- department runtime execution
- agent result return bus
- cross-venture resource scheduling
- checkpointing
- restart-safe recovery
- service supervision
- runtime incident classification/recovery
- continuous CEO cycles
- unified runtime status/control
- audit log
- health snapshot
- Termux runtime command script

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase1701_2000_persistent_autonomous_company_runtime.zip .
unzip -o companyos_phase1701_2000_persistent_autonomous_company_runtime.zip
bash companyos_phase1701_2000/install.sh ~/companyos

DEMO:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_phase2000_runtime_demo.py

CONTROL:
bash ~/companyos/scripts/companyos_runtime.sh status
bash ~/companyos/scripts/companyos_runtime.sh cycle
bash ~/companyos/scripts/companyos_runtime.sh recover
