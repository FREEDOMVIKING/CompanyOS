COMPANYOS PHASE 277-284
CONTINUOUS AUTONOMOUS IMPROVEMENT SUPERVISOR

277 Run-lock / overlap protection
278 Configurable continuous-cycle budgets
279 Repeated-failure tracker / breaker
280 Persistent improvement history
281 Cooldown-aware cycle scheduling
282 Supervised single-cycle wrapper
283 Continuous multi-cycle supervisor
284 Supervisor runtime/status

This builds on the proven:
- live OpenRouter generation,
- autonomous test repair,
- resilient output recovery,
- integration/regression gates,
- autonomous improvement planner.

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase277_284_continuous_improvement_supervisor.zip .
unzip -o companyos_phase277_284_continuous_improvement_supervisor.zip
bash companyos_phase277_284_continuous_improvement_supervisor/install.sh ~/companyos

EXPECTED:
phase277_284_verification_passed
phase284_continuous_supervisor_ready
3 passed
PHASE277_284_INSTALL_OK
CONTINUOUS_IMPROVEMENT_SUPERVISOR=READY

LIVE RUN:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_continuous_improvement.py

Defaults:
- max 3 improvement cycles per run
- 300 second cooldown between cycles
- stop after 3 consecutive failures

Override with:
COMPANYOS_MAX_CYCLES_PER_RUN
COMPANYOS_IMPROVEMENT_COOLDOWN_SECONDS
COMPANYOS_MAX_CONSECUTIVE_FAILURES

A live run may consume model credits.
