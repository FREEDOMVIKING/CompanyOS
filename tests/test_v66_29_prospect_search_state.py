from companyos.runtime.verified_web_prospect_discovery import retry_delay_for_result

def test_verified_search_gets_long_cooldown():
    assert retry_delay_for_result({
        "status":"DISCOVERY_COMPLETED",
        "verified_count":1,
        "search_candidate_count":3,
    }) >= 1800

def test_rejected_candidates_retry_sooner_than_verified_success():
    rejected=retry_delay_for_result({
        "status":"DISCOVERY_COMPLETED",
        "verified_count":0,
        "search_candidate_count":3,
    })
    success=retry_delay_for_result({
        "status":"DISCOVERY_COMPLETED",
        "verified_count":1,
        "search_candidate_count":3,
    })
    assert rejected < success

def test_http_error_does_not_get_success_cooldown():
    err=retry_delay_for_result({"status":"OPENAI_HTTP_500"})
    success=retry_delay_for_result({
        "status":"DISCOVERY_COMPLETED",
        "verified_count":1,
        "search_candidate_count":1,
    })
    assert err < success
