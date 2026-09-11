from companyos.failureops import FailureClassifier, VerificationPolicy, FailureOpsStatus

def test_failure_classifier():
    c = FailureClassifier().classify({}, {"success":False,"error":"unsupported_capability"})
    assert c["recoverable"] is True

def test_verification_policy():
    v = VerificationPolicy().verify({"job_id":"x"}, {"success":True,"capability":"test"})
    assert v["passed"] is True

def test_status():
    assert FailureOpsStatus().status()["success"] is True
