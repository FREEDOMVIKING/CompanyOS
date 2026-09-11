CompanyOS Phase 17001-17500
SPECIALIST CAPABILITY EXPANSION

This bundle replaces generic internal fallbacks for six core departments with
live-AI-backed specialist execution through the reasoning gateway already working
in your CompanyOS installation.

Departments:
- research
- finance
- product
- growth
- operations
- customer_success

Important boundaries:
- Research does not claim live web verification unless source data is supplied.
- Finance does not move money.
- Growth/customer-success do not send external messages.
- Product/operations do not deploy to production.
- Consequential external actions remain approval-gated.

INSTALL:
cd ~/companyos
cp /sdcard/Download/CompanyOS_SPECIALIST_CAPABILITIES_17500.zip .
unzip -o CompanyOS_SPECIALIST_CAPABILITIES_17500.zip
bash companyos_phase17001_17500/install.sh ~/companyos

VERIFY:
bash ~/companyos/scripts/companyos_specialists.sh verify

STATUS:
bash ~/companyos/scripts/companyos_specialists.sh status

RERUN CEO:
bash ~/companyos/scripts/companyos_ceo.sh run "Find the highest-value opportunity CompanyOS should research next"
