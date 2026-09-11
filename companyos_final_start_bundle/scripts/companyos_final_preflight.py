import json
from companyos.walletintegration.canonical_startup_gate import require_startup
r = require_startup()
print(json.dumps({"ready": True, "signer_gate": r, "transaction_sent": False}, indent=2))
