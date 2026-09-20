import json
from pathlib import Path
from tempfile import TemporaryDirectory

from companyos.governance.venture_identity_progression import (
    infer_stage,
    verified_external_stage,
    max_stage,
)

def test_successful_deployment_forces_launch():
    with TemporaryDirectory() as td:
        p=Path(td)
        build=p/"venture_stage_build.json"
        build.write_text("{}")
        dep=p/"deployment_result_live.json"
        dep.write_text(json.dumps({
            "schema":"companyos.real_deployment_result.v1",
            "connector":"hosting",
            "action":"deploy_production",
            "ok":True,
            "deployment_id":"dep-123",
            "live_url":"https://example.workers.dev",
        }))
        files=[build,dep]
        assert verified_external_stage(files)=="LAUNCH"
        assert infer_stage(files)=="LAUNCH"

def test_failed_deployment_does_not_advance():
    with TemporaryDirectory() as td:
        p=Path(td)
        dep=p/"deployment_result_failed.json"
        dep.write_text(json.dumps({
            "schema":"companyos.real_deployment_result.v1",
            "connector":"hosting",
            "action":"deploy_production",
            "ok":False,
        }))
        assert verified_external_stage([dep]) is None

def test_stage_is_monotonic():
    assert max_stage("BUILD","LAUNCH")=="LAUNCH"
    assert max_stage("LAUNCH_READY","LAUNCH")=="LAUNCH"
