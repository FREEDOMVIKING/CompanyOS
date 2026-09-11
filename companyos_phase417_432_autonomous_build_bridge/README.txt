COMPANYOS PHASE 417-432 — AUTONOMOUS BUILD BRIDGE

This bundle connects the Phase 401-416 venture factory contract to a bounded
autonomous build pipeline.

417 venture build intake
418 specialist dispatcher
419 isolated venture workspace
420 bounded build cycle
421 test/repair loop
422 artifact registry
423 release-candidate gate
424 KPI instrumentation
425 post-build review
426 portfolio scale/iterate/hold/pivot decision
427-431 autonomous builder bridge contract
432 execution runtime

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase417_432_autonomous_build_bridge.zip .
unzip -o companyos_phase417_432_autonomous_build_bridge.zip
bash companyos_phase417_432_autonomous_build_bridge/install.sh ~/companyos

EXPECTED:
phase417_432_verification_passed
phase432_autonomous_build_bridge_ready
3 passed
PHASE417_432_INSTALL_OK

After it passes, run the end-to-end dry demo:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_venture_to_build_demo.py
