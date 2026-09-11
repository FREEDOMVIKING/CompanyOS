COMPANYOS SELF-EVOLUTION SANDBOX IMPORT + RETRY REPAIR

Fixes:
ModuleNotFoundError during sandbox tests for generated sibling modules.

Install:
cd ~/companyos || exit 1
rm -rf companyos_self_evolution_sandbox_import_retry_repair_bundle
mkdir -p companyos_self_evolution_sandbox_import_retry_repair_bundle
unzip -o ~/storage/downloads/COMPANYOS_SELF_EVOLUTION_SANDBOX_IMPORT_RETRY_REPAIR_BUNDLE.zip -d ~/companyos/companyos_self_evolution_sandbox_import_retry_repair_bundle

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_self_evolution_sandbox_import_retry_repair_bundle/install.py
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_self_evolution_sandbox_import_retry_repair_bundle/verify.py

Run repair and retry:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_self_evolution_sandbox_retry_repair.py

Then check:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_self_evolution_runtime_status.py
