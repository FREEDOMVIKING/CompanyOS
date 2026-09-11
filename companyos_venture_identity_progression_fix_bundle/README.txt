COMPANYOS VENTURE IDENTITY + PROGRESSION FIX

Fixes:
- Duplicate venture identities caused by capitalization/naming differences.
- Internal support folders such as accounting being treated as ventures.
- Repeated unchanged artifact generation.
- Anti-stall goals now prefer advancing an existing stalled canonical venture to its next lifecycle step.

Preserves:
- Wallet config
- FULL_LIVE limits
- Consequential external approval gates
- Signer/reconciliation controls

Install:
cd ~/companyos
rm -rf companyos_venture_identity_progression_fix_bundle
mkdir -p companyos_venture_identity_progression_fix_bundle
unzip -o ~/storage/downloads/COMPANYOS_VENTURE_IDENTITY_PROGRESSION_FIX_BUNDLE.zip -d ~/companyos/companyos_venture_identity_progression_fix_bundle
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_venture_identity_progression_fix_bundle/install.py
python companyos_venture_identity_progression_fix_bundle/verify.py
bash scripts/companyos_productive_autonomy.sh restart
bash dashboard/venture_identity_progression_start.sh

Open http://127.0.0.1:8770
