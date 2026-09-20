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
    # Provider support can expand over time. The security contract is that
    # provider_status returns provider labels mapped only to boolean readiness,
    # never credential values. Provider labels may legitimately include words
    # such as "keyless".
    assert {"tavily", "brave", "serper"}.issubset(set(s))
    assert all(isinstance(k, str) and k for k in s)
    assert all(isinstance(v, bool) for v in s.values())
