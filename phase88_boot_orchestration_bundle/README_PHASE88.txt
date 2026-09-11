PHASE 88 — BOOT ORCHESTRATION

Purpose:
Create one production startup readiness sequence:

runtime env
-> RPC configured
-> wallet key configured
-> wallet derived
-> fresh live treasury balance
-> startup crash reconciliation
-> READY / BLOCKED

The boot sequence itself NEVER builds, signs, or broadcasts a transaction.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase88_boot_orchestration_bundle
mkdir -p phase88_boot_orchestration_bundle

unzip -o ~/storage/downloads/PHASE88_BOOT_ORCHESTRATION_BUNDLE.zip \
  -d ~/companyos/phase88_boot_orchestration_bundle

python ~/companyos/phase88_boot_orchestration_bundle/phase88_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase88_boot_orchestration_bundle/phase88_verify.py

RUN BOOT READINESS:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase88_boot_readiness.py

RUN FULL BOOT SEQUENCE:
bash ~/companyos/phase88_boot_sequence.sh
