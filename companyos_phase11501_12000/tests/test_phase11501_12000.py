from companyos.resilienceops import FailureDomainAnalyzer, DataIntegrityGuard, ResilienceAuthorityBoundary

def test_domains():
    assert FailureDomainAnalyzer().analyze([
        {"name":"a","failure_domain":"x"},{"name":"b","failure_domain":"y"}
    ])["single_domain_risk"] is False

def test_integrity():
    assert DataIntegrityGuard().evaluate([{"name":"x","passed":True}])["integrity_ok"]

def test_boundary():
    assert ResilienceAuthorityBoundary().evaluate({"kind":"bypass_approval"})["requires_approval"]
