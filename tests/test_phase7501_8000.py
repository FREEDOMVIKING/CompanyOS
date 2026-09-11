from companyos.liveexec import ExecutionJob, ApprovalExecutionBridge, RetryTimeoutPolicy

def test_job():
    assert ExecutionJob().create("research","internal_research")["status"]=="queued"

def test_gate():
    assert ApprovalExecutionBridge().split([ExecutionJob().create("deploy","production_deploy")])["approval_jobs"]

def test_retry():
    assert RetryTimeoutPolicy().decide("network",0)["retry"]
