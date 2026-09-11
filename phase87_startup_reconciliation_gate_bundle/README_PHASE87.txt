PHASE 87 — STARTUP RECONCILIATION GATE

Purpose:
- automatically run crash recovery before execution resumes
- block startup if any SUBMITTED record remains unresolved
- allow safe SIGNED/AUTHORIZED pending records without rebroadcast
- prevent ambiguous post-crash execution state from silently resuming

INSTALL:
cd ~/companyos || exit 1
rm -rf phase87_startup_reconciliation_gate_bundle
mkdir -p phase87_startup_reconciliation_gate_bundle

unzip -o ~/storage/downloads/PHASE87_STARTUP_RECONCILIATION_GATE_BUNDLE.zip \
  -d ~/companyos/phase87_startup_reconciliation_gate_bundle

python ~/companyos/phase87_startup_reconciliation_gate_bundle/phase87_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase87_startup_reconciliation_gate_bundle/phase87_verify.py

TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase87_startup_gate_test.py

RUNTIME STARTUP RECONCILIATION:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase87_startup_reconcile_runtime.py
