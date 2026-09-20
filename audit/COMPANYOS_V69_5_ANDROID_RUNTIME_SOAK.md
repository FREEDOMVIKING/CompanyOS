# CompanyOS V69.5 Android Runtime Soak

Overall status: **PASS**
Observed duration: **604.6 seconds**
Samples: **41**

## Supervisor stability
- Services observed: **19–19**
- Minimum running services: **19**
- Service restarts: **0**
- Maximum consecutive failures: **0**
- Signal 9 hits: **0**
- Force-kill hits: **0**

## Device pressure
- Peak CompanyOS RSS: **450.9 MB**
- RSS growth: **-0.6 MB**
- Minimum system MemAvailable: **3368.3 MB**
- Minimum system memory available ratio: **0.303869786402676**

## Queue
- Initial queued: **0**
- Final queued: **0**
- Maximum queued: **0**

## Safety
- The soak ran in an isolated detached Git worktree and temporary HOME.
- Python outbound socket connections were blocked.
- The real CompanyOS runtime state and real task queue were not used.
- No email, deployment, financial action, or transaction broadcast was performed.
