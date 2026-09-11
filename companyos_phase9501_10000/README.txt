CompanyOS Phase 9501-10000
AUTONOMOUS COMPANY PRODUCTION RUNTIME

This 500-phase push adds the unified production runtime layer:
- production runtime profile
- startup preflight
- system service graph
- production supervisor
- continuous discover→research→validate→build→launch→operate→optimize→portfolio cycle
- production mission scheduler/router
- approval queue bridge
- chained checkpoints
- production recovery manager
- unified observability
- production readiness gate
- persistent runtime state/audit
- unified CEO production runtime

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase9501_10000_autonomous_company_production_runtime.zip .
unzip -o companyos_phase9501_10000_autonomous_company_production_runtime.zip
bash companyos_phase9501_10000/install.sh ~/companyos

RUN:
bash ~/companyos/scripts/companyos_production.sh status
bash ~/companyos/scripts/companyos_production.sh verify
bash ~/companyos/scripts/companyos_production.sh cycle
