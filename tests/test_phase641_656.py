from companyos_phase641_656 import CustomerHealth, SupportTriage, IncidentManager

def test_customer_health():
    result=CustomerHealth().score({
        "usage_score":0.9,"value_realization":0.9,"satisfaction_score":0.9
    })
    assert result["status"]=="healthy"

def test_support_triage():
    ranked=SupportTriage().prioritize([
        {"id":"a","severity":"low"},
        {"id":"b","severity":"critical"}
    ])
    assert ranked[0]["id"]=="b"

def test_incident():
    assert IncidentManager().classify({"core_service_down":True})["requires_postmortem"] is True
