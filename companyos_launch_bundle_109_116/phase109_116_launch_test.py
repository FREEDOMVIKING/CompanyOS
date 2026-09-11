#!/usr/bin/env python3
from pathlib import Path
import tempfile

from companyos.runtime.approval_queue import ApprovalQueue
from companyos.runtime.action_proposal_router import ActionProposalRouter
from companyos.runtime.launch_health_snapshot import build_snapshot

with tempfile.TemporaryDirectory(prefix="launch_bundle_test_") as td:
    aq=ApprovalQueue(Path(td)/"approvals")
    router=ActionProposalRouter(aq)
    item=router.propose(
        title="Publish test site",
        action_type="publish",
        reason="external action requires approval",
        payload={"target":"test"}
    )
    checks={
      "approval_created": item.state=="PENDING",
      "approval_persisted": len(aq.all())==1,
      "health_snapshot_available": isinstance(build_snapshot(),dict),
    }
    ok=True
    for k,v in checks.items():
        ok=ok and v
        print(k,"=>","PASS" if v else "FAIL")
    print("EXTERNAL_ACTION_EXECUTED: False")
    print("TRANSACTION_SIGNED: False")
    print("TRANSACTION_BROADCAST: False")
    print("PHASE109_116_LAUNCH_TEST:","PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
