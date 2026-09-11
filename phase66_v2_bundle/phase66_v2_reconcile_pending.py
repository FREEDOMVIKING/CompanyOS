#!/usr/bin/env python3
import json
from companyos.walletintegration.pending_recovery import PendingTransactionRecovery

result = PendingTransactionRecovery().reconcile_all(limit=100)
print(json.dumps(result, indent=2, default=str))
