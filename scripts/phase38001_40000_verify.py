#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos.walletintegration import ExistingWalletBinding, OnChainReceiptVerifier, WalletIntegrationStatus

root = Path(tempfile.mkdtemp())
(root/"agents").mkdir()
(root/"agents"/"multichain_execution_adapter.py").write_text(
    "def execute(payload): return {'success':False,'status':'not_authorized'}\n"
)

binding = ExistingWalletBinding(root).inspect()
assert binding["multichain_adapter_present"] is True

ver = OnChainReceiptVerifier().verify({"success":True,"status":"confirmed","signature":"abc"})
assert ver["passed"] is True

status = WalletIntegrationStatus().status()
assert status["treasury_gate_mandatory"] is True
assert status["live_execution_auto_enabled"] is False

print(json.dumps({
    "success":True,
    "status":"phase38001_40000_verification_passed",
    "cycle_status":"phase40000_wallet_execution_wiring_ready",
    "live_execution_auto_enabled":False
}, indent=2))
