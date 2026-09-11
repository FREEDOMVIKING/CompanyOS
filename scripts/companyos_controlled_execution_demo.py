#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos.controlledexec import ControlledExecutionOrchestrator
from companyos.livegate import OneShotAuthorization

root = Path.home()/"companyos"

# Demo intentionally uses a fresh one-shot authorization and performs no broadcast.
auth = OneShotAuthorization(root).create(
    max_amount=0.001,
    destination="TEST_DESTINATION",
    ttl_seconds=300
)

orch = ControlledExecutionOrchestrator(
    root,
    max_single_amount=0.01,
    min_reserve=0.01
)

prepared = orch.prepare(
    token=auth["token"],
    destination="TEST_DESTINATION",
    amount=0.0001,
    balance=1.0,
    estimated_fee=0.00001,
    allowlist={"TEST_DESTINATION"},
    memo="controlled nonbroadcast validation"
)

print(json.dumps({
    "success":True,
    "status":"controlled_execution_demo_complete",
    "authorization":auth,
    "prepared":prepared
}, indent=2))
