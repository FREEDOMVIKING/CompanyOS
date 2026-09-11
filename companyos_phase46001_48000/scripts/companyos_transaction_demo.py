#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.transactionops import TransactionLifecycle

root = Path.home()/"companyos"

tx = TransactionLifecycle(
    root,
    max_single_amount=0.01,
    min_reserve=0.01
)

result = tx.prepare(
    destination="TEST_DESTINATION",
    amount=0.001,
    balance=1.0,
    estimated_fee=0.00001,
    allowlist={"TEST_DESTINATION"},
    memo="nonbroadcast validation"
)

print(json.dumps(result, indent=2))
