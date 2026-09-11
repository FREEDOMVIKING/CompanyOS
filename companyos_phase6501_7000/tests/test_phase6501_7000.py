from companyos.finalops import EndToEndRunner, RecoveryValidator, ApprovalBoundaryValidator
def test_e2e():
    assert EndToEndRunner().run(["discover","research","validate","build","launch","operate","optimize","portfolio_review"])["passed"]
def test_recovery():
    assert RecoveryValidator().validate([{"expected":"resume","actual":"resume"}])["passed"]
def test_approval():
    assert ApprovalBoundaryValidator().validate([{"kind":"bank_transfer","requires_approval":True}])["passed"]
