from types import SimpleNamespace
from companyos.runtime.execution_blocker_router import classify

def task(err,payload=None):
    return SimpleNamespace(
        task_id="t1",
        task_type="build",
        payload=payload or {"venture_id":"v1"},
        state="FAILED",
        attempts=3,
        max_attempts=3,
        last_error=err,
    )

def test_rate_limit_not_purchase():
    x=classify(task("HTTP 429 Too Many Requests"))
    assert x["classification"]=="WAIT_OR_ROTATE_PROVIDER"
    assert x["creates_procurement"] is False

def test_credential_gap_not_purchase():
    x=classify(task("API key missing"))
    assert x["classification"]=="CONNECT_OR_PROVISION_CREDENTIAL"
    assert x["creates_procurement"] is False

def test_connector_gap_prefers_internal_build():
    x=classify(task("missing connector for this capability"))
    assert x["classification"]=="BUILD_INTERNAL_CAPABILITY"
    assert x["creates_procurement"] is False

def test_explicit_paid_resource_can_be_procurement():
    x=classify(task(
        "subscription required",
        {
            "venture_id":"v1",
            "required_service":"transactional email delivery API",
            "quoted_price_usd":20,
        },
    ))
    assert x["classification"]=="EXTERNAL_PROCUREMENT_BLOCKER"
    assert x["creates_procurement"] is True
    assert x["required_resource"]=="transactional email delivery API"
    assert x["quoted_price_usd"]==20
