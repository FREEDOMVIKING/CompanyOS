from pathlib import Path

from companyos.runtime import live_market_intelligence as lmi
from companyos.runtime import multi_provider_research_pipeline as mpr


def test_evidence_query_contains_candidate_and_business_model():
    q=mpr._query(
        "Regional Construction AI",
        {
            "sector":"construction",
            "business_model":"subscription SaaS",
            "target_customer":"small contractors",
            "problem":"estimating delays",
            "offer":"estimating assistant",
        },
        "pricing",
        "",
    )
    low=q.lower()
    assert "regional construction ai" in low
    assert "subscription saas" in low
    assert "pricing" in low


def test_sparse_candidate_anchor_can_validate_when_requirement_matches():
    row={
        "url":"https://example.com/pricing",
        "title":"Construction software pricing guide",
        "content":"construction pricing subscription cost",
    }
    assert mpr._row_valid(row,{"construction"},"pricing") is True


def test_ensure_tasks_is_idempotent():
    q={"tasks":[]}
    candidates=[{
        "name":"Example Candidate",
        "path":Path("/tmp/example.json"),
        "payload":{},
        "priority":1,
    }]
    first=lmi.ensure_tasks(q,candidates)
    second=lmi.ensure_tasks(q,candidates)
    assert first==3
    assert second==0
    assert len(q["tasks"])==3


def test_market_topics_are_diverse():
    assert len(lmi.TOPICS)>=12
    assert len(set(lmi.TOPICS))==len(lmi.TOPICS)
    joined=" ".join(lmi.TOPICS).lower()
    assert "construction" in joined
    assert "healthcare" in joined
    assert "logistics" in joined
    assert "developer" in joined


def test_service_registered():
    from companyos.runtime.service_supervisor import ServiceSupervisor
    names={x.name for x in ServiceSupervisor.default_services()}
    assert "live_market_intelligence" in names
