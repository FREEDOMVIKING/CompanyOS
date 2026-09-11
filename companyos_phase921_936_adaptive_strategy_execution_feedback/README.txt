CompanyOS Phase 921-936
ADAPTIVE STRATEGY EXECUTION + VALIDATION FEEDBACK

Purpose:
Take the adaptive strategy created after stalled validation, execute it through
changed provider/query routes, keep only novel high-quality evidence, merge it
back into the venture, rerun validation, and measure whether confidence actually improves.

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase921_936_adaptive_strategy_execution_feedback.zip .
unzip -o companyos_phase921_936_adaptive_strategy_execution_feedback.zip
bash companyos_phase921_936_adaptive_strategy_execution_feedback/install.sh ~/companyos

DEMO:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_adaptive_strategy_execution_demo.py
