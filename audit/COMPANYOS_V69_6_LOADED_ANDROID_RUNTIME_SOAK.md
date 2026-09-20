# CompanyOS V69.6 Loaded Android Runtime Soak

Overall status: **PASS_WITH_WARNINGS**
Observed duration: **609.4 seconds**
Samples: **41**

## Workload
- Produced tasks: **1700**
- Completed tasks: **1586**
- Failed tasks: **0**
- Completion ratio: **0.933**
- Completion rate: **156.14/min**
- Maximum queued: **416**
- Final queued: **138**

## Supervisor stability
- Maximum supervised services: **19**
- Minimum running services: **19**
- Service restarts: **0**
- Maximum consecutive failures: **0**
- Signal 9 hits: **0**
- Force-kill hits: **0**

## Device pressure
- Peak CompanyOS RSS: **461.6 MB**
- RSS growth: **9.5 MB**
- Minimum system MemAvailable: **3133.9 MB**
- Minimum system memory available ratio: **0.2827236090378183**

## Safety
- Full supervisor ran in an isolated detached Git worktree and temporary HOME.
- Only internal research/planning/build tasks were injected.
- Python outbound socket connections were blocked.
- Profit auto-seeding was disabled.
- The real CompanyOS runtime and real task queue were not modified.
- No email, deployment, financial action, or transaction broadcast was performed.

## Warnings
- queue_not_fully_drained_by_soak_end
