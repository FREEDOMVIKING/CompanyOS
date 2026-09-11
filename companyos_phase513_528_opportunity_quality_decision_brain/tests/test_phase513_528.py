from companyos_phase513_528 import RelevanceFilter, SemanticDeduper, OpportunityQualityPipeline

def test_noise_rejected():
    records = [
        {"title":"Manual workflow software problem","text":"Business customers say it is slow and expensive"},
        {"title":"Ancient tomb painting","text":"Archaeology discovery"}
    ]
    result = RelevanceFilter().apply(records)
    assert len(result["accepted"]) == 1

def test_deduper():
    r = {"title":"Manual workflow issue","text":"Business workflow is slow"}
    assert len(SemanticDeduper().unique([r,r])) == 1

def test_pipeline():
    records = [
        {"source":"A","title":"Manual workflow is slow","text":"Business customers spend hours on manual workflow software and pricing is expensive.","url":"u1"},
        {"source":"B","title":"Workflow automation needed","text":"Teams want automation to replace manual software workflows.","url":"u2"},
    ]
    result = OpportunityQualityPipeline().run(records)
    assert result["success"] is True
    assert result["candidates"]
