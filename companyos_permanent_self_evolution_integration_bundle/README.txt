COMPANYOS PERMANENT SELF-EVOLUTION INTEGRATION

Purpose
-------
Make the repaired self-evolution flow permanent without depending on the older
tests_for() source layout that caused installer mismatches.

Permanent flow:
generated improvement
-> deterministic self-contained test generation
-> pre-promotion pytest validation
-> existing promotion engine
-> sandbox/import/tests
-> safe promotion into extension namespace
-> post-promotion health check
-> automatic rollback if unhealthy
-> permanent evolution ledger

This integration does NOT overwrite CompanyOS core files automatically.

INSTALL
-------
cd ~/companyos || exit 1

rm -rf companyos_permanent_self_evolution_integration_bundle
mkdir -p companyos_permanent_self_evolution_integration_bundle

unzip -o ~/storage/downloads/COMPANYOS_PERMANENT_SELF_EVOLUTION_INTEGRATION_BUNDLE.zip   -d ~/companyos/companyos_permanent_self_evolution_integration_bundle

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_permanent_self_evolution_integration_bundle/install.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_permanent_self_evolution_integration_bundle/verify.py

RUN ONCE
--------
bash scripts/companyos_permanent_self_evolution.sh once

START CONTINUOUSLY
------------------
bash scripts/companyos_permanent_self_evolution.sh start

STATUS
------
bash scripts/companyos_permanent_self_evolution.sh status

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_permanent_self_evolution_status.py
