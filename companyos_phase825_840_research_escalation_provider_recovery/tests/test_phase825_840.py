from companyos_phase825_840 import FailureClassifier, ProviderEscalationPolicy, AdaptiveBackoff

def test_failure_classifier():
    r=FailureClassifier().classify({"success":False,"error":"HTTP Error 403: rate limit exceeded"})
    assert r["kind"]=="rate_limited"

def test_escalation_policy():
    assert ProviderEscalationPolicy().decide({"kind":"rate_limited"},1,1)=="switch_provider"

def test_backoff():
    assert AdaptiveBackoff().seconds("timeout",1)==30
