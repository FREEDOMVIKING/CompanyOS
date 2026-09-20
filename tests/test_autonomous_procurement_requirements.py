from companyos.runtime.autonomous_procurement_requirements import extract

def test_detects_missing_payment_destination_without_fabricating():
    d = {
        "venture_id": "v1",
        "item": "hosting subscription",
        "vendor": "ExampleHost",
        "price_usd": 20,
        "expected_profit_30d": 100,
        "probability_estimate": 0.5,
        "evidence_count": 3,
    }
    x = extract(d, "test.json")
    assert x is not None
    assert x["ready_for_capital_intent"] is False
    assert "payment_destination" in x["missing_fields"]
    assert x["recipient"] is None

def test_complete_requirement_ready():
    d = {
        "venture_id": "v2",
        "item": "supplier inventory",
        "vendor": "VendorCo",
        "price_usd": 50,
        "recipient": "11111111111111111111111111111111",
        "expected_profit_usd": 200,
        "probability": 0.6,
        "evidence_count": 4,
    }
    x = extract(d, "test.json")
    assert x is not None
    assert x["ready_for_capital_intent"] is True
    assert x["missing_fields"] == []

def test_no_purchase_signal_is_ignored():
    d = {
        "venture_id": "v3",
        "title": "general market research",
        "expected_profit_30d": 100,
        "probability_estimate": 0.5,
        "evidence_count": 3,
    }
    assert extract(d, "test.json") is None
