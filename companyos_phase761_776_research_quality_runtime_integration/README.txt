COMPANYOS PHASE 761-776
RESEARCH QUALITY RUNTIME INTEGRATION

This bundle wires provider-aware evidence quality into the actual unified CEO research cycle.

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase761_776_research_quality_runtime_integration.zip .
unzip -o companyos_phase761_776_research_quality_runtime_integration.zip
bash companyos_phase761_776_research_quality_runtime_integration/install.sh ~/companyos

EXPECTED:
phase761_776_verification_passed
phase776_ceo_research_runtime_bridge_ready
3 passed
PHASE761_776_INSTALL_OK
CLOSED_LOOP_RESEARCH_QUALITY_PATCH=APPLIED

AFTER INSTALL:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_bounded_stress.py --rounds 3
