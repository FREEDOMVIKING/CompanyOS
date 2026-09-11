from companyos_phase369_384 import NoiseFilter, DescriptiveNamer, OpportunityIntelligenceCycle

def test_noise_filter():
    records = [
        {"title":"Manual workflow pain","text":"software is slow and expensive"},
        {"title":"Ancient tomb painting","text":"archaeology news"}
    ]
    result = NoiseFilter().apply(records)
    assert len(result["accepted"]) == 1

def test_namer():
    assert DescriptiveNamer().name("workflow_automation") == "Workflow Automation Copilot"

def test_intelligence_cycle():
    records = [
        {"source":"A","title":"Manual workflow is slow","text":"Business users spend hours on manual workflow software.","url":"u1"},
        {"source":"B","title":"Workflow pricing pain","text":"Customers say existing workflow software is expensive.","url":"u2"},
    ]
    result = OpportunityIntelligenceCycle().run(records)
    assert result["success"] is True
    assert result["market_theses"]
