COMPANYOS PHASE 841-856
AUTONOMOUS VALIDATION EXECUTION + EVIDENCE-TO-DECISION ENGINE

Purpose:
research -> validation mission -> hypotheses -> experiments -> evidence scoring ->
GO / REVISE / KILL -> build promotion when validated.

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase841_856_autonomous_validation.zip .
unzip -o companyos_phase841_856_autonomous_validation.zip
bash companyos_phase841_856_autonomous_validation/install.sh ~/companyos

EXPECTED:
phase841_856_verification_passed
phase856_autonomous_validation_decision_engine_ready
3 passed
PHASE841_856_INSTALL_OK

DEMO:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_validation_demo.py
