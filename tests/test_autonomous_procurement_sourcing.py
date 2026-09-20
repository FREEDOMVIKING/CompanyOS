from companyos.runtime.autonomous_procurement_sourcing import (
    build_query,
    price_candidates,
    provider_status,
)

def test_price_extraction():
    vals = price_candidates("Plan $19.99/month", "Setup $250")
    assert 19.99 in vals
    assert 250.0 in vals

def test_query_for_hosting():
    q = build_query({
        "item": "managed hosting",
        "category": "hosting",
        "missing_fields": ["vendor", "price"],
    })
    assert "pricing" in q.lower()

def test_provider_status_does_not_expose_keys():
    s = provider_status()
    assert set(s) == {"tavily", "brave", "serper"}
    assert all(isinstance(v, bool) for v in s.values())
