from pathlib import Path
from companyos.governance.venture_identity_progression import infer_stage, max_stage

def test_real_deployment_beats_historical_build_marker():
    files=[
        Path("/tmp/venture_stage_build.json"),
        Path("/tmp/companyos_progress/deployment_result_abc.json"),
    ]
    assert infer_stage(files)=="LAUNCH"

def test_customer_result_beats_launch():
    files=[
        Path("/tmp/deployment_result_abc.json"),
        Path("/tmp/customer_result_001.json"),
    ]
    assert infer_stage(files)=="CUSTOMER_ACQUISITION"

def test_monotonic_stage_helper():
    assert max_stage("LAUNCH","BUILD")=="LAUNCH"
    assert max_stage("CUSTOMER_ACQUISITION","LAUNCH")=="CUSTOMER_ACQUISITION"
