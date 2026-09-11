CompanyOS Phase 905-920
ADAPTIVE RESEARCH STRATEGY RECOVERY

Purpose:
When revalidation stalls, diagnose why confidence is flat, change query strategy,
change provider mix, target missing source classes, and retry only if the strategy
actually changed.

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase905_920_adaptive_research_strategy_recovery.zip .
unzip -o companyos_phase905_920_adaptive_research_strategy_recovery.zip
bash companyos_phase905_920_adaptive_research_strategy_recovery/install.sh ~/companyos

DEMO:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_adaptive_recovery_demo.py
