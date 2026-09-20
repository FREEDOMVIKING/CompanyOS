from companyos.runtime.openai_web_search_adapter import _qkey, cooldown_status
from companyos.runtime.autonomous_provider_accounts import candidate_retry_due

def test_query_key_stable():
    assert _qkey("  Official Pricing  ") == _qkey("official pricing")

def test_cooldown_status_shape():
    s=cooldown_status()
    assert "cooldown_active" in s
    assert "cooldown_remaining_seconds" in s

def test_pending_account_gets_cooldown():
    import time
    c={"domain":"example.com"}
    current={
        "example.com":{
            "status":"SIGNUP_DISCOVERY_PENDING",
            "timestamp_unix":time.time(),
        }
    }
    assert candidate_retry_due(c,current) is False
