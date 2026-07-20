COMPANYOS PHASE 261-268
AUTONOMOUS INTERNAL CAPABILITY-IMPROVEMENT LOOP

261 Internal health observer
262 Autonomous bounded improvement planner
263 Improvement -> capability mapper
264 Strict internal-only self-build mission generator
265 Verification-before-promotion policy
266 Persistent improvement learning recorder
267 Observe -> choose -> build -> verify -> learn autonomous improver
268 Continuous improvement runtime/status

This builds directly on the proven live-model self-builder from Phase 253-260.

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase261_268_autonomous_improvement_loop.zip .
unzip -o companyos_phase261_268_autonomous_improvement_loop.zip
bash companyos_phase261_268_autonomous_improvement_loop/install.sh ~/companyos

EXPECTED:
phase261_268_verification_passed
phase268_continuous_improvement_runtime_ready
3 passed
PHASE261_268_INSTALL_OK
AUTONOMOUS_IMPROVEMENT_LOOP=READY

After install, one live improvement cycle can be run with:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_autonomous_improvement_once.py

That live cycle can use OpenRouter and may consume API credits.
