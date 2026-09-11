PHASE 70 V2 — LAUNCH CONTROLLER + PRACTICE RUN

Install:
cd ~/storage/downloads || exit 1
unzip -o PHASE70_V2_LAUNCH_CONTROLLER_PRACTICE_BUNDLE.zip -d ~/companyos/phase70_v2_bundle
cd ~/companyos || exit 1
python phase70_v2_bundle/phase70_v2_install.py

Verify:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python phase70_v2_bundle/phase70_v2_verify.py

Practice run:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python phase70_practice_run.py

Status:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python phase70_status.py

Stop marker:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python phase70_stop.py

Practice run does NOT enable live financial execution and does NOT broadcast transactions.
Internal/reversible autonomy remains enabled for the practice controller.
