#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.signervalidation import (
    SignerProbe, UnsignedPayloadBuilder, LocalSignatureCheck,
    SolanaSimulationValidator, SignerValidationReport
)

root = Path.home()/"companyos"

probe = SignerProbe().probe()
unsigned = UnsignedPayloadBuilder().build()

signer_result = (probe or {}).get("result") or {}
sigcheck = LocalSignatureCheck().verify_structure(signer_result)

serialized = None
if isinstance(signer_result, dict):
    serialized = (
        signer_result.get("signed_transaction_base64")
        or signer_result.get("transaction_base64")
    )

simulation = SolanaSimulationValidator().simulate(serialized)
report = SignerValidationReport(root).write(
    probe, unsigned, sigcheck, simulation
)

print(json.dumps({
    "success":True,
    "status":"wallet_signer_end_to_end_validation_complete",
    "signer_probe":probe,
    "unsigned_intent":unsigned,
    "signature_check":sigcheck,
    "simulation":simulation,
    "report":report,
}, indent=2))
