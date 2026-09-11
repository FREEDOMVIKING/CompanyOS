CompanyOS Phase 15001-15500
AUTONOMOUS DAEMON + EVENT RUNTIME

Adds:
- persistent event bus
- durable job queue
- autonomous scheduler
- event-driven trigger routing
- restart recovery
- self-healing worker supervision
- heartbeat monitoring
- job leases
- dead-letter handling
- persistent daemon state/audit
- continuous CEO runtime loop
- Termux daemon start/stop/status/log controls

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase15001_15500_autonomous_daemon_event_runtime.zip .
unzip -o companyos_phase15001_15500_autonomous_daemon_event_runtime.zip
bash companyos_phase15001_15500/install.sh ~/companyos

VERIFY:
bash ~/companyos/scripts/companyos_daemon.sh verify
bash ~/companyos/scripts/companyos_daemon.sh tick

START CONTINUOUS RUNTIME:
bash ~/companyos/scripts/companyos_daemon_control.sh start

CHECK:
bash ~/companyos/scripts/companyos_daemon_control.sh status
bash ~/companyos/scripts/companyos_daemon_control.sh logs

STOP:
bash ~/companyos/scripts/companyos_daemon_control.sh stop
