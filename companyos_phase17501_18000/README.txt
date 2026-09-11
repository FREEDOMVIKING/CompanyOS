CompanyOS Phase 17501-18000
FAILURE CLOSURE + VERIFICATION RELIABILITY

Purpose:
Close the remaining internal execution gaps after Phase 17500.

Adds:
- failure classification
- generic AI-backed recovery for unsupported internal jobs
- recovery routing after specialist/provider failure
- more accurate execution verification
- preserved approval boundaries

This bundle is specifically aimed at reducing the remaining failed jobs in the
CEO cycle without pretending external actions happened.

INSTALL:
cd ~/companyos
cp /sdcard/Download/CompanyOS_FAILURE_CLOSURE_18000.zip .
unzip -o CompanyOS_FAILURE_CLOSURE_18000.zip
bash companyos_phase17501_18000/install.sh ~/companyos

VERIFY:
bash ~/companyos/scripts/companyos_failureops.sh verify

RERUN CEO:
bash ~/companyos/scripts/companyos_ceo.sh run "Find the highest-value opportunity CompanyOS should research next"
