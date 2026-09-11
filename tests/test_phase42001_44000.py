from companyos.signervalidation import LocalSignatureCheck, SignerValidationStatus

def test_signature_structure():
    assert LocalSignatureCheck().verify_structure({"signature":"abc"})["passed"] is True

def test_no_signature_fails():
    assert LocalSignatureCheck().verify_structure({})["passed"] is False

def test_safe_default():
    assert SignerValidationStatus().status()["ready_for_live_auto_enabled"] is False
