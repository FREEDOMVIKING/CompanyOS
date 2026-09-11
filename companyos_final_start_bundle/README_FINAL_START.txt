COMPANYOS FINAL START BUNDLE

This bundle finalizes startup around the already-verified canonical signer gate.

It does NOT create/replace private keys, print private keys, overwrite the wallet registry,
or enable unrestricted broadcast.

Install:
cd ~/companyos
unzip -o ~/storage/downloads/COMPANYOS_FINAL_START_BUNDLE.zip -d ~/companyos/companyos_final_start_bundle
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_final_start_bundle/install.py

Verify:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_final_start_bundle/verify.py

Smoke test:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_final_start_bundle/smoke_test.py

Control:
bash scripts/companyos_final_start.sh preflight
bash scripts/companyos_final_start.sh status
bash scripts/companyos_final_start.sh trial-check
bash scripts/companyos_final_start.sh full-check
bash scripts/companyos_final_start.sh start
bash scripts/companyos_final_start.sh stop
bash scripts/companyos_final_start.sh restart
bash scripts/companyos_final_start.sh logs
