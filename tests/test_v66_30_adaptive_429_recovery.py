from companyos.runtime.verified_web_prospect_discovery import (
    parse_retry_after_seconds,
    retry_delay_for_result,
)

def test_retry_seconds_from_message():
    x=parse_retry_after_seconds(None,"Please try again in 2.5s.")
    assert 2.4 <= x <= 2.6

def test_retry_milliseconds_from_message():
    x=parse_retry_after_seconds(None,"Please try again in 750ms.")
    assert 0.7 <= x <= 0.8

def test_429_uses_short_backoff():
    x=retry_delay_for_result({
        "status":"OPENAI_HTTP_429",
        "retry_after_seconds":3.0,
    })
    assert 5 <= x <= 20

def test_old_429_error_text_is_recovered():
    x=retry_delay_for_result({
        "status":"OPENAI_HTTP_429",
        "error":"Rate limit reached. Please try again in 4.2s.",
    })
    assert 5 <= x <= 20
