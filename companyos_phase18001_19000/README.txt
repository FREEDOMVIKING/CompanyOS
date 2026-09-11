CompanyOS Phase 18001-19000
CYCLE CLOSURE + POLICY-AWARE RESOLUTION

This bundle fixes the verification semantics seen in the previous CEO cycle.

A job can now resolve as:
- completed
- deferred_for_approval
- deduplicated
- failed

cycle_verified becomes true only when:
- every job is resolved, AND
- there are zero unresolved failures.

Approval-gated work is NOT falsely marked as executed.
It is marked resolved/deferred_for_approval.

This makes the final cycle summary honest:
completed work stays completed,
safe deferments stay deferments,
and real failures remain failures.

INSTALL:
cd ~/companyos
cp /sdcard/Download/CompanyOS_CYCLE_CLOSURE_19000.zip .
unzip -o CompanyOS_CYCLE_CLOSURE_19000.zip
bash companyos_phase18001_19000/install.sh ~/companyos

VERIFY:
bash ~/companyos/scripts/companyos_cycleops.sh verify

RERUN CEO:
bash ~/companyos/scripts/companyos_ceo.sh run "Find the highest-value opportunity CompanyOS should research next"
