from companyos.runtime.atomic_launch_executor import validate

def test_validate_rejects_wrong_connector():
    action={
        "connector":"smtp",
        "action":"deploy_production",
        "payload":{"canonical_id":"x"},
    }
    out=validate("x",{"deploy_root":"/definitely/missing"},action)
    assert "not_hosting_connector" in out["reasons"]

def test_validate_rejects_wrong_action():
    action={
        "connector":"hosting",
        "action":"send_email",
        "payload":{"canonical_id":"x"},
    }
    out=validate("x",{"deploy_root":"/definitely/missing"},action)
    assert "not_deploy_production" in out["reasons"]
