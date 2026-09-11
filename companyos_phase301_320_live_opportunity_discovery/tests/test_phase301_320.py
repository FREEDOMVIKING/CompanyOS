from companyos_phase301_320 import ResearchIngestor, CEODiscoveryLoop, SourceContract

def test_source_contract():
    assert SourceContract().normalize({"source":"x","title":"y","text":"z"})["valid"] is True

def test_ingestor_dedupes():
    r = {"source":"x","title":"y","text":"manual painful workflow","url":"u"}
    assert len(ResearchIngestor().ingest([r, r])["records"]) == 1

def test_discovery_loop():
    result = CEODiscoveryLoop().run([
        {"source":"x","title":"Manual work is slow","text":"Customers struggle with slow manual reporting.","url":"u1"},
        {"source":"y","title":"Pricing pain","text":"Teams complain competitor pricing is expensive.","url":"u2"},
    ])
    assert result["success"] is True
    assert result["ranked_opportunities"]
