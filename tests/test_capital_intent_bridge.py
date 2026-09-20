from companyos.runtime.capital_intent_bridge import (
    explicit_capital_fields,
    normalize_probability,
)

def test_probability_percent_normalizes():
    assert normalize_probability(25) == 0.25

def test_no_recipient_means_no_intent():
    d = {
        "amount_sol": 0.1,
        "expected_profit_30d": 50,
        "probability_estimate": 0.5,
        "evidence_count": 3,
        "venture_id": "v1",
    }
    assert explicit_capital_fields(d) is None

def test_no_amount_means_no_intent():
    d = {
        "recipient": "11111111111111111111111111111111",
        "expected_profit_30d": 50,
        "probability_estimate": 0.5,
        "evidence_count": 3,
        "venture_id": "v1",
    }
    assert explicit_capital_fields(d) is None

def test_complete_explicit_request_extracts():
    d = {
        "recipient": "11111111111111111111111111111111",
        "amount_sol": 0.1,
        "expected_profit_30d": 50,
        "probability_estimate": 0.5,
        "evidence_count": 3,
        "venture_id": "v1",
        "purpose": "buy required service",
    }
    x = explicit_capital_fields(d)
    assert x is not None
    assert x["recipient"] == d["recipient"]
    assert x["amount_sol"] == 0.1
