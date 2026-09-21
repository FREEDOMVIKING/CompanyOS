# CompanyOS V69.12 Candidate Output Materialization Forensics

Overall forensic run: **PASS**
Primary choke point: **split_runtime_roots_plus_non_candidate_specialist_outputs**

## Runtime-root topology
- Canonical runtime: `/data/data/com.termux/files/home/.companyos_runtime`
- Repo-local runtime: `/data/data/com.termux/files/home/companyos/.companyos_runtime`
- Same underlying directory: **False**
- Task queue root: `/data/data/com.termux/files/home/.companyos_runtime/task_queue`
- Specialist evidence root: `/data/data/com.termux/files/home/.companyos_runtime/specialist_evidence`
- Candidate-materializer runtime: `/data/data/com.termux/files/home/companyos/.companyos_runtime`
- Research-capture runtime: `/data/data/com.termux/files/home/companyos/.companyos_runtime`

## Output inspection
- Recent completed orchestrations inspected: **12**
- Completed stage tasks inspected: **36**
- Candidate-shaped task results: **0**
- Candidate-shaped specialist artifacts: **0**
- Missing referenced artifacts: **0**

## Static findings
- Research specialist explicitly says external research performed = false: **True**
- Research capture wraps `start`: **True**
- Research capture wraps `cycle`: **False**
- Research capture wraps `run_until_terminal`: **False**
- Synthetic candidate parser control passed: **True**

## Diagnoses
- **split_runtime_roots** (high): CEO queue and specialist evidence use ~/.companyos_runtime while candidate/capture modules use ~/companyos/.companyos_runtime. Effect: Materializers/capture can miss the actual specialist outputs unless roots are bridged or explicitly scanned.
- **research_handler_is_intake_validator_not_research_executor** (high): default research specialist writes supplied evidence and external_research_performed=False. Effect: A CEO research stage can complete without generating market/economic candidate evidence.
- **capture_scope_ends_at_orchestrator_start** (high): research_output_capture wraps AutonomousCEOOrchestrator.start only. Effect: Start-time capture occurs before research/planning/build stage handlers execute, so later specialist returns are not captured by that wrapper.
- **completed_tasks_without_candidate_shaped_output** (high): 36 completed stage tasks inspected; zero candidate-shaped task results and zero candidate-shaped artifacts. Effect: Downstream candidate materializers have no qualifying economics-bearing records to normalize.
