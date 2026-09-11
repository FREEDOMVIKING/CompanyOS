COMPANYOS PHASE 705-720
UNIFIED AUTONOMOUS CEO RUNTIME

705 persistent unified runtime state
706 system registry
707 shared context bus
708 governed action router
709 mission execution wrapper
710 outcome normalization bridge
711 lifecycle feedback bridge
712 strategic learning bridge
713 portfolio feedback bridge
714 integration audit
715 runtime health
716 closed-loop mission cycle
717 persistent queue execution
718 runtime supervisor + safe mode
719 CEO runtime bridge
720 runtime/status

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase705_720_unified_autonomous_ceo_runtime.zip .
unzip -o companyos_phase705_720_unified_autonomous_ceo_runtime.zip
bash companyos_phase705_720_unified_autonomous_ceo_runtime/install.sh ~/companyos

EXPECTED:
phase705_720_verification_passed
phase720_unified_autonomous_ceo_runtime_ready
3 passed
PHASE705_720_INSTALL_OK
UNIFIED_AUTONOMOUS_CEO_RUNTIME=READY

STATUS:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/unified_runtime_status.py

SAFE ONE-TICK TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_unified_ceo_tick.py

This phase focuses on integration: mission -> outcome -> lifecycle -> learning -> next mission,
with persistent state, portfolio feedback, governance checks, audit trails, and safe-mode supervision.
