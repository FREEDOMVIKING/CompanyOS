from companyos.hardening import HealthMatrix, SecretReferenceAudit, RollbackManager

def test_health():
    assert HealthMatrix().evaluate([{"heartbeat":True,"error_rate":0,"saturation":0,"backlog":0}])["healthy"]

def test_secrets():
    assert not SecretReferenceAudit().inspect({"api_key":"plaintext"})["safe"]

def test_rollback():
    assert RollbackManager().plan({"previous_artifact":"v1"})["ready"]
