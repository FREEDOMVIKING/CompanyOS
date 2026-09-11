COMPANYOS FULL AUTONOMY BUNDLE

Install:
cd ~/companyos
rm -rf companyos_full_autonomy_bundle
mkdir -p companyos_full_autonomy_bundle
unzip -o ~/storage/downloads/COMPANYOS_FULL_AUTONOMY_BUNDLE.zip -d ~/companyos/companyos_full_autonomy_bundle
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_full_autonomy_bundle/install.py
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_full_autonomy_bundle/verify.py

Activate:
bash scripts/companyos_full_autonomy.sh activate

Start:
bash scripts/companyos_full_autonomy.sh start

Status:
bash scripts/companyos_full_autonomy.sh status

Logs:
bash scripts/companyos_full_autonomy.sh logs

Stop:
bash scripts/companyos_full_autonomy.sh stop

This enables persistent autonomous CEO operation, continuous goal creation, delegation,
research, planning, building, evaluation, follow-up and self-improvement.
Existing signer verification, live transaction limits, reserve rules, allowlists,
approval gates for consequential/irreversible actions, and reconciliation remain in force.
