#!/usr/bin/env python
from __future__ import annotations
import sys, os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)) if str(ROOT) not in sys.path else None
for line in (ROOT/".env").read_text(errors="ignore").splitlines():
    if line.strip() and not line.lstrip().startswith("#") and "=" in line:
        k,v=line.split("=",1); os.environ[k.strip()]=v.strip().strip(chr(34)).strip(chr(39))

from companyos.scheduler_financial_queue_bridge import queue_scheduler_financial_intent
from companyos.runtime_financial_queue import pending_items, complete
from companyos.walletintegration.solana_signer_key_adapter import load_signer_material

m=load_signer_material(os.environ["SOLANA_PRIVATE_KEY"],
                       os.getenv("SOLANA_PRIVATE_KEY_ENCODING","auto"))
intent={"action_type":"sol_transfer","destination":m.public_address,
        "sol":0,"source_ref":"AUTOWIRE_INSTALL_TEST"}
a=queue_scheduler_financial_intent(intent)
b=queue_scheduler_financial_intent(intent)
print("ENQUEUE: PASS")
print("DEDUPLICATION:", "PASS" if a.idempotency_key==b.idempotency_key else "FAIL")
print("SOL:",a.sol)
print("SIGNING: NOT PERFORMED")
print("BROADCAST: NOT REQUESTED")
complete(a,{"mode":"installation_validation","signed":False,"broadcast":False})
print("PENDING:",len(pending_items()))
