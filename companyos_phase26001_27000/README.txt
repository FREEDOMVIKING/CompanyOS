CompanyOS Phase 26001-27000
AUTONOMOUS CEO FINANCIAL DECISION LOOP

This phase adds the decision layer between opportunity discovery and treasury execution.

Flow:
Opportunity
 -> financial plan
 -> expected-value analysis
 -> risk adjustment
 -> capital allocation
 -> reserve preservation
 -> treasury authorization
 -> dry-run / approval / blocked / later-live execution

Important:
The AI does NOT control or bypass treasury hard limits.
Treasury rules remain outside the decision engine.

This phase does not automatically enable live financial execution.

INSTALL:
cd ~/companyos
cp /sdcard/Download/CompanyOS_FINANCIAL_DECISION_LOOP_27000.zip .
unzip -o CompanyOS_FINANCIAL_DECISION_LOOP_27000.zip
bash companyos_phase26001_27000/install.sh ~/companyos

VERIFY:
bash ~/companyos/scripts/companyos_ceo_finops.sh verify

DEMO:
bash ~/companyos/scripts/companyos_ceo_finops.sh demo

STATUS:
bash ~/companyos/scripts/companyos_ceo_finops.sh status
