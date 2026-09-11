from companyos.finops import FinancialIntent, FinancialSafetyValidator

def test_intent_normalization():
    i = FinancialIntent("solana",1,"dest","test").normalize()
    assert i["chain"] == "solana"
    assert i["idempotency_key"]

def test_validator_accepts_dry_run():
    v = FinancialSafetyValidator().validate({
        "status":"dry_run_authorized",
        "idempotency_key":"abc"
    })
    assert v["passed"] is True
