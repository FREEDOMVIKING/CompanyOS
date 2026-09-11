#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos.walletautobind import ExistingWalletLocator, WalletBindingWriter, WalletActivationReadiness, WalletAutobindStatus

root = Path(tempfile.mkdtemp())
(root/"agents").mkdir()
p = root/"agents"/"multichain_execution_adapter.py"
p.write_text(
    "MULTICHAIN_SIGNER_COMMAND='env'\n"
    "wallet_address='TEST_PUBLIC_ADDRESS'\n"
    "def execute(payload): return {'success':False,'status':'not_authorized'}\n"
)

best = ExistingWalletLocator(root).best()
assert best is not None
assert best["name"] == "multichain_execution_adapter.py"

binding = WalletBindingWriter(root).write(best, metadata={"private_keys_copied":False})
assert binding["success"] is True
assert binding["binding"]["contains_private_key_material"] is False

ready = WalletActivationReadiness(root).evaluate({"passed":True})
assert ready["ready_for_dry_run"] is True
assert ready["ready_for_live"] is False

status = WalletAutobindStatus().status()
assert status["private_key_material_copied"] is False
assert status["live_execution_auto_enabled"] is False

print(json.dumps({
    "success":True,
    "status":"phase40001_42000_verification_passed",
    "cycle_status":"phase42000_existing_wallet_autobind_and_solana_preflight_ready"
}, indent=2))
