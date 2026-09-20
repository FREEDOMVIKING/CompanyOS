from companyos.runtime.procurement_evidence_verifier import (
    denied, same_site, tokens, _price_candidates
)

def test_rejects_yahoo_news_source():
    assert denied("finance.yahoo.com") is True

def test_same_site_subdomain():
    assert same_site("app.example.com","example.com") is True
    assert same_site("example.com","evil.com") is False

def test_item_tokens_drop_generic_words():
    t=tokens("Marketplace Software Opportunity domain registration")
    assert "marketplace" not in t
    assert "software" not in t

def test_contextual_price_prefers_relevant_window():
    text="Random article mentions $999. Domain registration .com pricing is $12.99 per year."
    rows=_price_candidates(text,["registration"],"domain")
    assert rows
    assert rows[0]["value_usd"]==12.99
