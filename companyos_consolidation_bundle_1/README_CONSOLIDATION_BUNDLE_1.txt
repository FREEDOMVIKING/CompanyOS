COMPANYOS CONSOLIDATION BUNDLE 1
Canonical Execution Gateway

Non-destructive consolidation layer.
Defaults remain non-broadcast. Does not touch wallet keys or enable external actions.

Install:
cd ~/companyos
unzip -o ~/storage/downloads/COMPANYOS_CONSOLIDATION_BUNDLE_1.zip -d ~/companyos/companyos_consolidation_bundle_1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_consolidation_bundle_1/install.py

Verify:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_consolidation_bundle_1/verify.py

Smoke test:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_consolidation_bundle_1/smoke_test.py
