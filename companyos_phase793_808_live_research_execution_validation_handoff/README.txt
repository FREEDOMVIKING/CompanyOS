COMPANYOS PHASE 793-808
LIVE MULTI-PROVIDER RESEARCH EXECUTION + VALIDATION HANDOFF

This phase wires Phase 777-792 into the live unified CEO research cycle.

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase793_808_live_research_execution_validation_handoff.zip .
unzip -o companyos_phase793_808_live_research_execution_validation_handoff.zip
bash companyos_phase793_808_live_research_execution_validation_handoff/install.sh ~/companyos

EXPECTED:
phase793_808_verification_passed
phase808_live_research_execution_validation_handoff_ready
3 passed
PHASE793_808_INSTALL_OK
UNIFIED_CLOSED_LOOP_PATCH=APPLIED

DEMO:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_live_research_demo.py

THEN RETEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_bounded_stress.py --rounds 3
