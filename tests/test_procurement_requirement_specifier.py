from companyos.runtime.procurement_requirement_specifier import generic_item, informative_tokens

def test_generic_software_api_blocked():
    assert generic_item("software_api requirement","software_api") is True

def test_specific_requirement_allowed():
    assert generic_item("real-time cryptocurrency market price data API","software_api") is False

def test_generic_words_removed():
    t=informative_tokens("Marketplace Software Opportunity API Requirement")
    assert "software" not in t
    assert "requirement" not in t
