CompanyOS Phase 9001-9500
AUTONOMOUS EXTERNAL ACTION GOVERNANCE

This 500-phase push adds:
- centralized action policy engine
- persistent approval queue
- action risk scoring
- budget enforcement
- action rate limiting
- dual-control policy
- dry-run simulation
- change-set construction
- post-action verification
- rollback planning
- human override registry
- persistent governance state/audit
- unified CEO action-governance controller

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase9001_9500_autonomous_external_action_governance.zip .
unzip -o companyos_phase9001_9500_autonomous_external_action_governance.zip
bash companyos_phase9001_9500/install.sh ~/companyos

RUN:
bash ~/companyos/scripts/companyos_action_governance.sh status
bash ~/companyos/scripts/companyos_action_governance.sh verify
bash ~/companyos/scripts/companyos_action_governance.sh cycle
