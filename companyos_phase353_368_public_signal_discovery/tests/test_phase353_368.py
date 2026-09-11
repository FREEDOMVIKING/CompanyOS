from companyos_phase353_368 import CustomerPainFilter, SignalQuality, SourceBackoff

def test_pain_filter():
    assert CustomerPainFilter().apply([{
        "title":"manual workflow","text":"slow and difficult","source":"x"
    }])

def test_quality():
    r = {
        "title":"x","text":"a"*100,"url":"u","source":"GitHub Issues",
        "pain_terms":["manual"],"metadata":{"comments":1}
    }
    assert SignalQuality().score(r) >= 5

def test_backoff():
    assert SourceBackoff().next_delay(3) > SourceBackoff().next_delay(1)
