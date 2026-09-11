CompanyOS Venture Lifecycle Progression

Purpose:
- Detect repeated/duplicate work.
- Infer each venture's observed lifecycle stage.
- Show whether artifacts changed since the previous observation.
- State the next meaningful lifecycle action.
- Does NOT change financial limits or automatically bypass external-action approvals.

Install:
cd ~/companyos
rm -rf companyos_lifecycle_progression_bundle
mkdir -p companyos_lifecycle_progression_bundle
unzip -o ~/storage/downloads/COMPANYOS_LIFECYCLE_PROGRESSION_BUNDLE.zip -d ~/companyos/companyos_lifecycle_progression_bundle
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_lifecycle_progression_bundle/install.py
python companyos_lifecycle_progression_bundle/verify.py
bash dashboard/lifecycle_progress_start.sh

Open http://127.0.0.1:8769
