COMPANYOS STALLED-STAGE PROGRESSION FIX

Fixes:
1. Version aliases such as _v1 / -v2 are folded into the parent canonical venture.
2. The productive-autonomy watchdog prioritizes stalled canonical ventures.
3. CUSTOMER_ACQUISITION stalls become concrete internal/reversible task chains instead of repeated recommendations.

Preserved:
- existing financial limits
- wallet configuration
- signer/reconciliation controls
- consequential external-action approval gates

Install:

cd ~/companyos || exit 1

rm -rf companyos_stalled_stage_progression_fix_bundle
mkdir -p companyos_stalled_stage_progression_fix_bundle

unzip -o ~/storage/downloads/COMPANYOS_STALLED_STAGE_PROGRESSION_FIX_BUNDLE.zip \
  -d ~/companyos/companyos_stalled_stage_progression_fix_bundle

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python companyos_stalled_stage_progression_fix_bundle/install.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python companyos_stalled_stage_progression_fix_bundle/verify.py

Restart only the productive-autonomy watchdog:

bash scripts/companyos_productive_autonomy.sh restart

Then check:

bash scripts/companyos_productive_autonomy.sh status
