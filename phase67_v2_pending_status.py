#!/usr/bin/env python3
import json
from companyos.walletintegration.reconciliation_worker import PendingReconciliationWorker

result = PendingReconciliationWorker().inspect()
print(json.dumps(result, indent=2, default=str))
