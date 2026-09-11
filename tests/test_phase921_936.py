from companyos_phase921_936 import NovelEvidenceFilter,ConfidenceImprovementGate,DiminishingReturnGuard
def test_novelty():
    assert NovelEvidenceFilter().apply([{"id":"a"}],[{"id":"b"}])["novelty"]==1.0
def test_gain():
    assert ConfidenceImprovementGate().evaluate(.5,.55)["improved"] is True
def test_diminishing():
    h=[{"confidence_delta":0.0,"novelty":0.0},{"confidence_delta":0.01,"novelty":0.1}]
    assert DiminishingReturnGuard().evaluate(h)["stop"] is True
