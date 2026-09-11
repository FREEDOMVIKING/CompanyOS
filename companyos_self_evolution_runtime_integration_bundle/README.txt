COMPANYOS SELF-EVOLUTION RUNTIME INTEGRATION

Connects existing CompanyOS continuous-improvement output to the installed Self-Evolution Promotion Engine.

Flow:
generated improvement -> automatic discovery -> sandbox tests -> safe promotion into companyos/evolution_promoted/ -> health check -> rollback if unhealthy -> persistent ledger

IMPORTANT: It does not overwrite CompanyOS core files automatically.

INSTALL
cd ~/companyos || exit 1
rm -rf companyos_self_evolution_runtime_integration_bundle
mkdir -p companyos_self_evolution_runtime_integration_bundle
unzip -o ~/storage/downloads/COMPANYOS_SELF_EVOLUTION_RUNTIME_INTEGRATION_BUNDLE.zip -d ~/companyos/companyos_self_evolution_runtime_integration_bundle
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_self_evolution_runtime_integration_bundle/install.py
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_self_evolution_runtime_integration_bundle/verify.py

RUN ONCE
bash scripts/companyos_self_evolution_runtime.sh once

START CONTINUOUSLY
bash scripts/companyos_self_evolution_runtime.sh start

STATUS
bash scripts/companyos_self_evolution_runtime.sh status
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_self_evolution_runtime_status.py
