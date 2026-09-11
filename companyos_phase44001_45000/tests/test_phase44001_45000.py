from companyos.signercompat import SanitizedDiagnostics, SignerCompatStatus

def test_redaction():
    out = SanitizedDiagnostics().sanitize({"secret":"x","safe":"y"})
    assert out["secret"] == "***REDACTED***"
    assert out["safe"] == "y"

def test_safe_default():
    assert SignerCompatStatus().status()["live_execution_auto_enabled"] is False
