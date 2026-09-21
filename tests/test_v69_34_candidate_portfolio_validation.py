from companyos.runtime import candidate_portfolio_validation as cpv
from companyos.runtime.profit_opportunity_engine import Opportunity


def _op(
    name,
    category,
    score,
    evidence_quality=50,
    coverage=0.4,
    critical=0.25,
):
    return Opportunity(
        id=name.lower().replace(" ","_"),
        name=name,
        source=f"/tmp/{name}.json",
        mechanism="subscription",
        category=category,
        next_action="validate demand",
        expected_profit=10000,
        margin=50,
        time_to_cash_days=30,
        capital_required=1000,
        capital_at_risk=500,
        probability=50,
        evidence_count=2,
        evidence_quality=evidence_quality,
        scalability=60,
        reversibility=80,
        readiness=50,
        complexity=40,
        compliance_risk=10,
        dependency_risk=20,
        score=score,
        payload={
            "observed_evidence_coverage":coverage,
            "critical_evidence_coverage":critical,
            "missing_evidence_requirements":["buyer_demand","pricing"],
        },
    )


def test_portfolio_selection_diversifies_categories(monkeypatch):
    rows=[
        _op("A","construction",80),
        _op("B","construction",79),
        _op("C","healthcare",70),
        _op("D","logistics",65),
    ]
    monkeypatch.setattr(cpv.poe,"discover",lambda:rows)
    selected=cpv.select_portfolio(3)
    assert len(selected)==3
    assert len({x["category"] for x in selected})==3


def test_experiment_targets_missing_critical_requirement():
    candidate=cpv.candidate_record(_op("A","construction",80))
    exp=cpv.experiment_for(candidate)
    assert exp["requirement"]=="buyer_demand"
    assert exp["max_cost_usd"]==0.0
    assert exp["external_message_allowed"] is False
    assert exp["financial_action_allowed"] is False
    assert exp["deployment_allowed"] is False


def test_ensure_experiments_idempotent():
    queue={"experiments":[]}
    candidate=cpv.candidate_record(_op("A","construction",80))
    assert cpv.ensure_experiments(queue,[candidate])==1
    assert cpv.ensure_experiments(queue,[candidate])==0
    assert len(queue["experiments"])==1


def test_execute_experiment_requires_candidate_relevant_rows(monkeypatch,tmp_path):
    candidate=cpv.candidate_record(_op("A","construction",80))
    exp=cpv.experiment_for(candidate)

    monkeypatch.setattr(cpv,"ARTIFACT_DIR",tmp_path/"artifacts")
    monkeypatch.setattr(cpv,"EVIDENCE_QUEUE",tmp_path/"evidence_queue.json")
    monkeypatch.setattr(
        cpv.pcr,
        "search_web",
        lambda q,max_results=8:{
            "provider":"public_research_mesh",
            "results":[
                {
                    "source":"source_a",
                    "title":"A construction buyer demand report",
                    "url":"https://example.com/a",
                    "content":"A construction buyer demand customers adoption",
                },
                {
                    "source":"source_b",
                    "title":"A construction customer adoption study",
                    "url":"https://example.org/b",
                    "content":"A construction customers adoption demand",
                },
            ],
            "attempts":[],
        },
    )
    monkeypatch.setattr(
        cpv,
        "_valid_rows",
        lambda candidate,requirement,rows:rows,
    )

    out=cpv.execute_experiment(exp,candidate)
    assert out["status"]=="passed"
    assert out["distinct_url_count"]==2

    evidence=cpv.load(cpv.EVIDENCE_QUEUE,{"tasks":[]})
    assert evidence["tasks"][0]["status"]=="observed"


def test_portfolio_score_does_not_mutate_economics():
    op=_op("A","construction",80)
    before=(op.expected_profit,op.probability)
    _=cpv.portfolio_score(op)
    after=(op.expected_profit,op.probability)
    assert before==after
