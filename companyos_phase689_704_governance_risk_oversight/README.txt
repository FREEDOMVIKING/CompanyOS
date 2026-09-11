COMPANYOS PHASE 689-704
AUTONOMOUS GOVERNANCE, RISK CONTROLS + EXECUTIVE OVERSIGHT

689 authority matrix
690 risk classification
691 approval gateway
692 delegated budgets
693 financial exposure limits
694 external action policy
695 least-privilege secrets policy
696 agent permission boundaries
697 preflight checks
698 rollback requirements
699 safe mode
700 policy violation detection
701 human escalation queue
702 decision provenance
703 governance ledger
704 runtime/status

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase689_704_governance_risk_oversight.zip .
unzip -o companyos_phase689_704_governance_risk_oversight.zip
bash companyos_phase689_704_governance_risk_oversight/install.sh ~/companyos

EXPECTED:
phase689_704_verification_passed
phase704_governance_risk_oversight_ready
3 passed
PHASE689_704_INSTALL_OK
AUTHORITY_MATRIX=READY
APPROVAL_GATEWAY=READY
SAFE_MODE=READY
GOVERNANCE_LEDGER=READY

DEMO:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_governance_demo.py

STATUS:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/governance_status.py
