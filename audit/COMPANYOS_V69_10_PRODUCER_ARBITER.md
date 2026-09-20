# CompanyOS V69.10 Serialized Profit-First Producer Arbiter

Overall status: **PASS**
Shared handoff: **60 seconds**
CEO root starts observed: **6**
Minimum inter-start gap: **60.09129524230957**
Spacing pass: **True**

## Producer callers
- `candidate_materialization_bridge.py:347:maybe_recover_missing_outputs`: **2**
- `profit_first_enrichment_expansion.py:176:dispatch`: **2**
- `profit_first_research_pipeline.py:107:run_stage`: **2**

## Runtime stability
- Native tasks total: **18**
- Native task states: `{"COMPLETED": 15, "QUEUED": 3}`
- Service restarts: **0**
- Consecutive failures: **0**
- Signal 9 hits: **0**
- Memory-error hits: **0**
