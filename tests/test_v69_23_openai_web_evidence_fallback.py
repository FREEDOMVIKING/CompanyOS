from companyos.runtime import openai_web_evidence_fallback as ow
from companyos.runtime import autonomous_evidence_acquisition as aea

def test_extracts_url_citation_context():
    response={
        "output":[{
            "type":"message",
            "content":[{
                "type":"output_text",
                "text":"Concrete estimating software costs 99 dollars monthly. Source.",
                "annotations":[{
                    "type":"url_citation",
                    "url":"https://vendor.example/pricing",
                    "title":"Pricing",
                    "start_index":53,
                    "end_index":60,
                }],
            }],
        }]
    }
    rows=ow._annotation_rows(response)
    assert len(rows)==1
    assert rows[0]["url"]=="https://vendor.example/pricing"
    assert "Concrete" in rows[0]["context"]

def test_no_citation_means_no_evidence_rows():
    response={"output":[{"type":"message","content":[{"type":"output_text","text":"Unsupported claim.","annotations":[]}]}]}
    assert ow._annotation_rows(response)==[]

def test_internal_candidate_name_alone_no_longer_passes_candidate_match():
    row={
        "source":"example.com",
        "url":"https://example.com/x",
        "title":"regional_construction_ai",
        "summary":"A generic unrelated product has pricing.",
    }
    anchors={"construction","concrete","estimating","workflow"}
    assert aea._row_matches_candidate(row,"regional_construction_ai",anchors) is False

def test_real_candidate_concepts_can_pass_candidate_match():
    row={
        "source":"example.com",
        "url":"https://example.com/x",
        "title":"Construction estimating",
        "summary":"Concrete contractors use estimating workflow tools.",
    }
    anchors={"construction","concrete","estimating","workflow"}
    assert aea._row_matches_candidate(row,"regional_construction_ai",anchors) is True
