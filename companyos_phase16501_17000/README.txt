CompanyOS Phase 16501-17000
AUTONOMOUS CEO + LIVE INTELLIGENCE INTEGRATION

This package connects the proven live reasoning path into the CEO runtime:

objective
  -> live AI reasoning gateway
  -> structured JSON planning
  -> specialist department delegation
  -> durable job queue
  -> worker execution
  -> verification
  -> persistent learning memory
  -> next cycle

Safety/authority behavior:
- Internal research, analysis, building, and bounded optimization can be delegated.
- Consequential external actions remain approval-gated.
- The package does not contain or overwrite your OpenRouter API key.
- It reuses ~/.companyos_runtime/live_intelligence.env if already present.
- Verification uses a local mock reasoning server and does not spend API credits.

INSTALL:
cd ~/companyos
cp /sdcard/Download/CompanyOS_AUTONOMOUS_CEO_17000.zip .
unzip -o CompanyOS_AUTONOMOUS_CEO_17000.zip
bash companyos_phase16501_17000/install.sh ~/companyos

START LIVE REASONING:
bash ~/companyos/scripts/companyos_reasoning_control.sh start

TEST LIVE REASONING:
bash ~/companyos/scripts/companyos_reasoning_control.sh test

RUN CEO PLAN + INTERNAL EXECUTION:
bash ~/companyos/scripts/companyos_ceo.sh run "Find the highest-value opportunity CompanyOS should research next"

PLAN ONLY:
bash ~/companyos/scripts/companyos_ceo.sh plan "Create a plan to improve customer retention"

STATUS:
bash ~/companyos/scripts/companyos_ceo.sh status
