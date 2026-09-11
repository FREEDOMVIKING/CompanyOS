from companyos_phase745_760 import ProviderSelector,DedupeEvidence,ResearchStopPolicy
def test_provider_selection():
    r=ProviderSelector().choose([{"name":"a","availability":0.2},{"name":"b","availability":1.0}])
    assert r["selected"]["name"]=="b"
def test_dedupe():
    assert len(DedupeEvidence().dedupe([{"url":"x"},{"url":"x"}]))==1
def test_stop():
    assert ResearchStopPolicy().decide({"complete":True},0.8,1)["stop"] is True
