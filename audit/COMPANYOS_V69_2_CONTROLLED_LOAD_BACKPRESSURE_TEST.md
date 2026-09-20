# CompanyOS V69.2 Controlled Load + Backpressure Wiring Test

Overall status: **PASS**
Load scaling: **PASS**
Execution batch consumer present: **True**
Producer divisor consumer present: **True**

## Controlled load tiers
- LOW (100 queued): divisor=1, batch=16, completed=16, failed=0, rate=1173.6/min, status=PASS
- MEDIUM (300 queued): divisor=2, batch=32, completed=32, failed=0, rate=969.5/min, status=PASS
- HIGH (600 queued): divisor=3, batch=48, completed=48, failed=0, rate=829.3/min, status=PASS
- CRITICAL (900 queued): divisor=4, batch=64, completed=64, failed=0, rate=1347.5/min, status=PASS

## Wiring
- `execution_batch` references: .companyos_runtime/self_evolution/worktrees/20260920T182249Z/companyos/companyos/runtime/adaptive_backpressure.py, .companyos_runtime/self_evolution/worktrees/20260920T182249Z/companyos/companyos/runtime/autonomous_ceo_orchestrator.py, .companyos_runtime/self_evolution/worktrees/20260920T182249Z/companyos/companyos/runtime/continuous_goal_runtime.py, companyos/runtime/adaptive_backpressure.py, companyos/runtime/autonomous_ceo_orchestrator.py, companyos/runtime/continuous_goal_runtime.py, scripts/companyos_v69_1_adaptive_throughput_benchmark.py, scripts/companyos_v69_2_controlled_load_backpressure_test.py
- `producer_divisor` references: .companyos_runtime/self_evolution/worktrees/20260920T182249Z/companyos/companyos/runtime/adaptive_backpressure.py, .companyos_runtime/self_evolution/worktrees/20260920T182249Z/companyos/companyos/runtime/productive_autonomy_watchdog.py, companyos/runtime/adaptive_backpressure.py, companyos/runtime/productive_autonomy_watchdog.py, scripts/companyos_v69_1_adaptive_throughput_benchmark.py, scripts/companyos_v69_2_controlled_load_backpressure_test.py

The benchmark uses an isolated temporary HOME and does not modify the real CompanyOS task queue.
No external web research, email, deployment, transaction, or financial action is performed.
