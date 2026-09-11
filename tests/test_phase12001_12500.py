from companyos.governanceops import ComplianceMatrix, AccessReviewEngine, GovernanceAuthorityBoundary

def test_matrix():
    assert ComplianceMatrix().map([{"requirement":"x","required_controls":["a"]}],["a"])[0]["compliant"]

def test_access():
    assert AccessReviewEngine().review([{"identity":"x","admin":False,"mfa":False}])["passed"]

def test_boundary():
    assert GovernanceAuthorityBoundary().evaluate({"kind":"approve_policy_exception"})["requires_approval"]
