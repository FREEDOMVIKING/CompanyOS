CompanyOS Phase 20001-21000
AUTONOMOUS RECOVERY + RE-VERIFICATION

This bundle targets the unresolved jobs seen in the Phase 20000 autonomous cycle.

Adds:
- diagnosis of unresolved execution results
- missing-input recovery using bounded internal assumptions
- bounded retries for transient/execution failures
- automatic re-execution of recoverable work
- automatic re-verification after recovery

It does NOT bypass approval boundaries or invent external facts/actions.

INSTALL:
cd ~/companyos
cp /sdcard/Download/CompanyOS_AUTONOMOUS_RECOVERY_21000.zip .
unzip -o CompanyOS_AUTONOMOUS_RECOVERY_21000.zip
bash companyos_phase20001_21000/install.sh ~/companyos

VERIFY:
bash ~/companyos/scripts/companyos_recovery.sh verify

RERUN ONE AUTONOMOUS CYCLE:
bash ~/companyos/scripts/companyos_autonomy.sh run --cycles 1
