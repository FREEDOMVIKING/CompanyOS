CompanyOS Phase 889-904
MULTI-ROUND AUTONOMOUS REVALIDATION ORCHESTRATOR

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase889_904_multi_round_revalidation_orchestrator.zip .
unzip -o companyos_phase889_904_multi_round_revalidation_orchestrator.zip
bash companyos_phase889_904_multi_round_revalidation_orchestrator/install.sh ~/companyos

DEMO:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_multi_round_revalidation_demo.py

Goal:
REVISE -> targeted research -> revalidate -> repeat automatically until
GO/build, KILL/archive, HUMAN_REVIEW, or bounded exhaustion.
