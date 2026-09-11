COMPANYOS PHASE 745-760
PROVIDER-AWARE RESEARCH ORCHESTRATION + EVIDENCE QUALITY CONTROL

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase745_760_provider_aware_research_orchestration.zip .
unzip -o companyos_phase745_760_provider_aware_research_orchestration.zip
bash companyos_phase745_760_provider_aware_research_orchestration/install.sh ~/companyos

EXPECTED:
phase745_760_verification_passed
phase760_provider_aware_research_quality_ready
3 passed
PHASE745_760_INSTALL_OK

DEMO:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_research_quality_demo.py
