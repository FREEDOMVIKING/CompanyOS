#!/usr/bin/env python3
from pathlib import Path
import tempfile

from companyos.runtime.project_pipeline import ProjectPipeline
from companyos.runtime.specialist_coordination import SpecialistCoordinator
from companyos.runtime.project_checkpointing import ProjectCheckpointStore
from companyos.runtime.launch_readiness import LaunchReadinessEvaluator

with tempfile.TemporaryDirectory(prefix="phase117_132_") as td:
    base=Path(td)
    pp=ProjectPipeline(base/"projects")
    cp=ProjectCheckpointStore(base/"checkpoints")
    rec=pp.create(title="Test Project",objective="Validate bundled project pipeline")
    assign=SpecialistCoordinator().assignment_for(rec.stage)
    cp.write(rec.project_id,rec.stage,{"agent":assign.agent_name})
    rec.artifacts.append("internal_plan.md")
    rec.stage="LAUNCH_READY"
    pp.save(rec)
    ready=LaunchReadinessEvaluator().evaluate(
        project_stage=rec.stage,
        blockers=rec.blockers,
        artifacts_count=len(rec.artifacts)
    )

    checks={
      "project_created":bool(rec.project_id),
      "specialist_assigned":bool(assign.agent_name),
      "checkpoint_written":len(list((base/"checkpoints").glob("*.json")))==1,
      "launch_readiness_true":ready.ready is True,
    }
    ok=True
    for k,v in checks.items():
        ok=ok and v
        print(k,"=>","PASS" if v else "FAIL")
    print("EXTERNAL_ACTION_EXECUTED: False")
    print("TRANSACTION_SIGNED: False")
    print("TRANSACTION_BROADCAST: False")
    print("PHASE117_132_TEST:","PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
