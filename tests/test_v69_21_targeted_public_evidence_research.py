from companyos.runtime import targeted_public_evidence_research as tr

CANDIDATE={
    "name":"regional_construction_ai",
    "market":"construction",
    "target_customer":"regional concrete contractors",
    "problem":"estimating and bid workflow inefficiency",
    "offer":"AI bid workflow automation",
    "business_model":"subscription software",
}

def test_pricing_queries_are_candidate_specific():
    queries=tr.build_queries(CANDIDATE,"pricing")
    text=" ".join(queries).lower()
    assert "construction" in text
    assert "pricing" in text or "cost" in text
    assert len(queries)>=3

def test_buyer_queries_are_candidate_specific():
    queries=tr.build_queries(CANDIDATE,"buyer_demand")
    text=" ".join(queries).lower()
    assert "construction" in text
    assert "customer" in text or "adoption" in text or "case study" in text

def test_generic_unrelated_page_rejected():
    anchors=tr.candidate_terms(CANDIDATE,CANDIDATE["name"])
    ok,hits=tr.page_supports_requirement(
        "Photo editing pricing",
        "A consumer photo editor costs 10 dollars per month.",
        "pricing",
        anchors,
    )
    assert ok is False

def test_construction_pricing_page_can_qualify():
    anchors=tr.candidate_terms(CANDIDATE,CANDIDATE["name"])
    ok,hits=tr.page_supports_requirement(
        "Construction estimating software pricing",
        "Concrete contractors use construction estimating and bid workflow tools. Pricing plans cost 99 dollars per month.",
        "pricing",
        anchors,
    )
    assert ok is True
    assert len(hits)>=2

def test_candidate_metadata_is_not_required_inside_source_excerpt():
    anchors=tr.candidate_terms(CANDIDATE,CANDIDATE["name"])
    ok,_=tr.page_supports_requirement(
        "Contractor estimating customer case study",
        "Concrete contractors adopted estimating workflow software. Customers report using it for bid preparation.",
        "buyer_demand",
        anchors,
    )
    assert ok is True
