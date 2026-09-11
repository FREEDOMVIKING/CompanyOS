from companyos.liveintegration import ConnectorCertification, RequestSanitizer, LiveModeGate, LivePreflight

def test_certification():
    c=ConnectorCertification().certify({
        "name":"x","enabled":True,"capabilities":["research"],"health_score":.9,
        "credentials_ready":True,"fallback_ready":True,"receipts_enabled":True})
    assert c["certified"]

def test_redaction():
    assert RequestSanitizer().sanitize({"password":"secret"})["password"]=="***REDACTED***"

def test_gate():
    p=LivePreflight().evaluate({"connector_certified":True,"credentials_ready":True,"health_ok":True,"rollback_ready":True,"audit_ready":True})
    assert not LiveModeGate().evaluate({"kind":"bank_transfer"},p,approval=False)["allowed"]
