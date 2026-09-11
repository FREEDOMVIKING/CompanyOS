from companyos_phase857_872 import ValidationGapAnalyzer, EvidenceMerger, BoundedRevalidationLoop
def test_gaps():
    assert ValidationGapAnalyzer().analyze({"scores":{"validation_confidence":.5}})
def test_merge():
    assert len(EvidenceMerger().merge([{"id":"a"}],[{"id":"a"},{"id":"b"}]))==2
def test_bound():
    assert BoundedRevalidationLoop().evaluate(3,"REVISE",False)["continue"] is False
