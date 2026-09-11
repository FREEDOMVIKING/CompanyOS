CompanyOS Phase 2601-3000
UNIFIED AUTONOMOUS COMPANY CONTROL PLANE

This 400-phase bundled push adds:
- event bus
- persistent CEO daemon
- event-driven department loops
- venture lifecycle supervision
- multi-venture portfolio allocation
- budget governance
- resource governance
- deadlock detection
- self-health monitoring
- checkpoint management
- restart coordination
- command routing
- unified control API
- runtime guardrails
- control-plane audit

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase2601_3000_unified_autonomous_company_control_plane.zip .
unzip -o companyos_phase2601_3000_unified_autonomous_company_control_plane.zip
bash companyos_phase2601_3000/install.sh ~/companyos

DEMO:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_phase3000_controlplane_demo.py

CONTROL:
bash ~/companyos/scripts/companyos_control.sh status
bash ~/companyos/scripts/companyos_control.sh cycle
bash ~/companyos/scripts/companyos_control.sh verify
