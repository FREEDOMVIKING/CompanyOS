COMPANYOS PHASE 561-576
BUSINESS EXECUTION + PORTFOLIO INTELLIGENCE

561 business case engine
562 venture scorecard
563 stage evidence requirements
564 commitment gate
565 launch readiness
566 operating KPIs
567 portfolio comparison
568 bounded attention allocation
569 kill / iterate / scale policy
570 milestone engine
571 execution audit
572 mission audit bridge
573 business execution manager
574 portfolio intelligence
575 CEO execution bridge
576 runtime/status

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase561_576_business_execution_portfolio_intelligence.zip .
unzip -o companyos_phase561_576_business_execution_portfolio_intelligence.zip
bash companyos_phase561_576_business_execution_portfolio_intelligence/install.sh ~/companyos

EXPECTED:
phase561_576_verification_passed
phase576_business_execution_portfolio_intelligence_ready
3 passed
PHASE561_576_INSTALL_OK
BUSINESS_EXECUTION_MANAGER=READY
PORTFOLIO_INTELLIGENCE=READY
MISSION_AUDIT_BRIDGE=READY

DEMO:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_business_execution_review.py
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_portfolio_intelligence.py
