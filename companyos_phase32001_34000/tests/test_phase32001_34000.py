from companyos.executionops import ExecutionVerifier, ExecutionOpsStatus

def test_verified_execution_requires_evidence():
    v = ExecutionVerifier().verify({"success":True})
    assert v["passed"] is False

def test_verified_execution_with_output():
    v = ExecutionVerifier().verify({"success":True,"output":"done"})
    assert v["passed"] is True

def test_status():
    assert ExecutionOpsStatus().status()["false_completion_prevention"] is True
