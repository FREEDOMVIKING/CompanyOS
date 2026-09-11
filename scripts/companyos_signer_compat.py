#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.signercompat import (
    SignerContractDetector,
    SignerRequestBridge,
    SignerCompatibilityValidation
)

root = Path.home()/"companyos"
detector = SignerContractDetector(root).inspect()
bridge = SignerRequestBridge().compatibility_probe()
report = SignerCompatibilityValidation(root).write(detector, bridge)

print(json.dumps({
    "success": True,
    "status": "signer_compatibility_bridge_complete",
    "detector": detector,
    "bridge": bridge,
    "report": report
}, indent=2))
