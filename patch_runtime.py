from pathlib import Path
cfg=Path.home()/"companyos"/"companyos"/"controlplane"/"config.py"
if not cfg.exists():raise SystemExit("Missing controlplane config.py")
text=cfg.read_text(encoding="utf-8")
if "roadmap_execution_bridge_70001_80000" in text:
    print("Services already registered.");raise SystemExit(0)
needle='ServiceSpec("supervisor_18301_18400", "companyos.controlplane.supervisor", True),'
if needle not in text:raise SystemExit("Supervisor registration not found")
cfg.write_text(text.replace(needle,"""        ServiceSpec("roadmap_execution_bridge_70001_80000", "companyos.roadmap_execution_bridge.runtime", True),
        ServiceSpec("milestone_generator_v3_70001_80000", "companyos.milestone_generator_v3.runtime", True),
        ServiceSpec("specialist_assignment_v3_70001_80000", "companyos.specialist_assignment_v3.runtime", True),
        ServiceSpec("venture_artifact_pipeline_70001_80000", "companyos.venture_artifact_pipeline.runtime", True),
        ServiceSpec("execution_evidence_linker_70001_80000", "companyos.execution_evidence_linker.runtime", True),
        ServiceSpec("progress_sync_v3_70001_80000", "companyos.progress_sync_v3.runtime", True),
        ServiceSpec("venture_validation_engine_70001_80000", "companyos.venture_validation_engine.runtime", True),
        ServiceSpec("launch_readiness_engine_70001_80000", "companyos.launch_readiness_engine.runtime", True),
        ServiceSpec("dashboard_cluster_manager_70001_80000", "companyos.dashboard_cluster_manager.runtime", True),
        ServiceSpec("execution_recovery_manager_70001_80000", "companyos.execution_recovery_manager.runtime", True),
        """+needle),encoding="utf-8")
print("Registered 10 roadmap-execution services.")
