#!/usr/bin/env python3
import json
from companyos.walletintegration.reconciliation_worker import PendingReconciliationWorker

result = PendingReconciliationWorker().run_once(limit=100)
print(json.dumps(result, indent=2, default=str))
