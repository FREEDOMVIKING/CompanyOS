from pathlib import Path

from companyos.runtime import evidence_coverage_rescoring as ecr
from companyos.runtime import live_market_intelligence as lmi
from companyos.runtime.profit_opportunity_engine import Opportunity, score


def test_core_requirements_include_decision_critical_evidence():
    assert lmi.DEFAULT_REQUIREMENTS==("buyer_demand","pricing","competition")
    assert set(("buyer_demand","pricing","provenance","corroboration")).issubset(
        set(lmi.EVIDENCE_GAP_REQUIREMENTS)
    )
    assert "competition" in lmi.EVIDENCE_GAP_REQUIREMENTS


def test_evidence_metrics_coverage(monkeypatch,tmp_path):
    artifacts=[]
    for i,(req,source) in enumerate((
        ("buyer_demand","source_a"),
        ("pricing","source_b"),
        ("provenance","source_c"),
    )):
        p=tmp_path/f"a{i}.json"
        p.write_text(
            '{"source_rows":[{"source":"%s","url":"https://example.com/%s","observed_at":9999999999}]}' % (source,i),
            encoding="utf-8",
        )
        artifacts.append((req,p))

    q={"tasks":[
        {
            "candidate_name":"Test Candidate",
            "requirement":req,
            "status":"observed",
            "evidence_artifacts":[{"path":str(path)}],
        }
        for req,path in artifacts
    ]}

    m=ecr.evidence_metrics("Test Candidate",q,now=9999999999)
    assert m["coverage"]==0.6
    assert m["critical_coverage"]==0.75
    assert m["unique_source_count"]==3
    assert m["evidence_quality_score"]>0


def test_apply_metrics_does_not_change_economics(tmp_path):
    p=tmp_path/"candidate.json"
    payload={
        "name":"Candidate",
        "expected_profit":75,
        "probability_of_success":40,
    }
    p.write_text("{}",encoding="utf-8")

    invariant=ecr.apply_metrics(
        p,
        payload,
        {
            "observed_task_count":2,
            "observed_requirements":["buyer_demand","pricing"],
            "coverage":0.4,
            "critical_coverage":0.5,
            "missing_requirements":["provenance","corroboration","competition"],
            "evidence_row_count":4,
            "artifact_count":2,
            "evidence_quality_score":55.0,
            "source_diversity_score":50.0,
            "freshness_score":100.0,
        },
    )

    assert invariant["economics_unchanged"] is True
    assert payload["expected_profit"]==75
    assert payload["probability_of_success"]==40


def test_profit_engine_score_responds_to_verified_evidence_quality():
    base=Opportunity(
        id="a",
        name="A",
        source="test",
        expected_profit=10000,
        margin=50,
        time_to_cash_days=30,
        capital_required=1000,
        capital_at_risk=500,
        probability=50,
        evidence_count=0,
        evidence_quality=0,
        scalability=50,
        reversibility=70,
        readiness=50,
        complexity=40,
        compliance_risk=10,
        dependency_risk=20,
    )
    supported=Opportunity(
        **{
            **base.__dict__,
            "id":"b",
            "evidence_count":5,
            "evidence_quality":80,
        }
    )

    low=score(base).score
    high=score(supported).score
    assert high>low


def test_candidate_priority_prefers_evidence_gaps(monkeypatch,tmp_path):
    monkeypatch.setattr(lmi,"CANDIDATES",tmp_path)

    complete=tmp_path/"complete.json"
    gap=tmp_path/"gap.json"

    complete.write_text(
        '{"name":"Complete","expected_profit":50,"observed_evidence_count":5,"observed_evidence_coverage":1.0,"critical_evidence_coverage":1.0}',
        encoding="utf-8",
    )
    gap.write_text(
        '{"name":"Gap","expected_profit":50,"observed_evidence_count":1,"observed_evidence_coverage":0.2,"critical_evidence_coverage":0.0}',
        encoding="utf-8",
    )

    rows=lmi.candidate_rows()
    assert rows[0]["name"]=="Gap"
