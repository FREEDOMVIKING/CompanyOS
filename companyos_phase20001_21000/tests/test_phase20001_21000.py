from companyos.recoveryops import DiagnosticEngine, RetryPolicy, MissingInputHandler

def test_missing_input_diagnosis():
    d = DiagnosticEngine().diagnose({}, {"success":False,"message":"Need more information"}, {"passed":False})
    assert d["kind"] == "missing_input"

def test_retry_bound():
    d = {"kind":"transient_failure","recoverable":True}
    assert RetryPolicy().decision(d, 0)["retry"] is True
    assert RetryPolicy().decision(d, 2)["retry"] is False

def test_enrichment():
    j = MissingInputHandler().enrich({"payload":{"instruction":"x"}})
    assert j["payload"]["recovery_enriched"] is True
