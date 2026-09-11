CompanyOS Phase 1251-1450 — Multi-Agent Departments + Executive Delegation

Adds:
- persistent executive memory
- research, product, growth, sales, finance, operations, customer-success departments
- CEO-level delegation/orchestration
- shared cross-department context
- authority gates for irreversible/high-risk external actions
- approval queue
- Termux installer, tests, and demo

Install:
cd ~/companyos
cp /sdcard/Download/companyos_phase1251_1450_multi_agent_departments.zip .
unzip -o companyos_phase1251_1450_multi_agent_departments.zip
bash companyos_phase1251_1450/install.sh ~/companyos

Demo:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_phase1251_1450_demo.py
