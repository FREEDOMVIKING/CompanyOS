COMPANYOS PHASE 593-608
STRATEGIC LEARNING + ADAPTIVE MISSION REPLANNING

593 lesson extraction
594 persistent hypothesis store
595 hypothesis updates
596 strategy state
597 strategy adjustment
598 mission rewriting
599 experiment memory
600 recurring failure patterns
601 recurring success patterns
602 portfolio learning
603 confidence updates
604 learning audit
605 adaptive replanner
606 CEO learning bridge
607 learning health
608 runtime/status

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase593_608_strategic_learning_adaptive_replanning.zip .
unzip -o companyos_phase593_608_strategic_learning_adaptive_replanning.zip
bash companyos_phase593_608_strategic_learning_adaptive_replanning/install.sh ~/companyos

EXPECTED:
phase593_608_verification_passed
phase608_strategic_learning_adaptive_replanning_ready
3 passed
PHASE593_608_INSTALL_OK
STRATEGIC_LEARNING=READY
ADAPTIVE_REPLANNER=READY

DEMO:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_strategic_learning_demo.py
