COMPANYOS IDLE-CYCLE RECOVERY FIX V2

Corrects the failed first patch.

Your watchdog uses:
    def tick() -> dict[str, Any]:

V2 supports that annotated signature, verifies the recovery hook is actually inside tick(),
and reseeds the already-idle baseline so recovery can become eligible immediately.

Install:

cd ~/companyos || exit 1

rm -rf companyos_idle_cycle_recovery_fix_v2_bundle
mkdir -p companyos_idle_cycle_recovery_fix_v2_bundle

unzip -o ~/storage/downloads/COMPANYOS_IDLE_CYCLE_RECOVERY_FIX_V2_BUNDLE.zip \
  -d ~/companyos/companyos_idle_cycle_recovery_fix_v2_bundle

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python companyos_idle_cycle_recovery_fix_v2_bundle/install.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python companyos_idle_cycle_recovery_fix_v2_bundle/verify.py

bash scripts/companyos_productive_autonomy.sh restart

sleep 10

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python scripts/companyos_idle_recovery_status.py

Watch:
http://127.0.0.1:8768

Look for:
IDLE_CYCLE_RECOVERY
