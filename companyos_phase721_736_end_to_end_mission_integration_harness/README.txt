COMPANYOS PHASE 721-736
END-TO-END AUTONOMOUS MISSION INTEGRATION + STRESS TEST HARNESS

721 controlled test mission factory
722 queue injector
723 cycle probe
724 lifecycle probe
725 learning probe
726 audit probe
727 state probe
728 queue probe
729 integration assertions
730 safe fault injector
731 recovery probe
732 bounded stress plan
733 end-to-end harness
734 stress runner
735 concise integration report
736 runtime/status

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase721_736_end_to_end_mission_integration_harness.zip .
unzip -o companyos_phase721_736_end_to_end_mission_integration_harness.zip
bash companyos_phase721_736_end_to_end_mission_integration_harness/install.sh ~/companyos

EXPECTED:
phase721_736_verification_passed
phase736_end_to_end_mission_integration_harness_ready
3 passed
PHASE721_736_INSTALL_OK
END_TO_END_MISSION_HARNESS=READY

RUN ONE CONTROLLED END-TO-END TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_end_to_end_harness.py

OPTIONAL BOUNDED STRESS TEST AFTER SINGLE TEST PASSES:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_bounded_stress.py --rounds 3
