#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos.signervalidation import LocalSignatureCheck, SignerValidationReport, SignerValidationStatus

sig = LocalSignatureCheck().verify_structure({"signature":"abc","public_key":"xyz"})
assert sig["passed"] is True

root = Path(tempfile.mkdtemp())
report = SignerValidationReport(root).write(
    {"success":True},
    {"success":True},
    {"passed":True},
    {"passed":True,"broadcast_attempted":False}
)
assert report["ready_for_live_review"] is True
assert report["ready_for_live"] is False

status = SignerValidationStatus().status()
assert status["broadcast_disabled_during_validation"] is True
assert status["ready_for_live_auto_enabled"] is False

print(json.dumps({
    "success":True,
    "status":"phase42001_44000_verification_passed",
    "cycle_status":"phase44000_wallet_signer_end_to_end_validation_ready"
}, indent=2))
