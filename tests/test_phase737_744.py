from companyos_phase737_744 import RateLimitDetector,RetryClassifier,BackoffPolicy
def test_rate_limit(): assert RateLimitDetector().detect("HTTP Error 403: rate limit exceeded")["rate_limited"]
def test_retry():
    r=RetryClassifier().classify({"success":False,"error":"HTTP Error 403: rate limit exceeded"}); assert r["retryable"] and not r["hard_failure"]
def test_backoff(): assert BackoffPolicy().delay_seconds(2)==120
