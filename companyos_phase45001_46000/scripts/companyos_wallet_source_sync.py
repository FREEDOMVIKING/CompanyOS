#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.walletsource import VerifiedWalletIdentity, ProposalSourceInjector, ExecutionSourceGuard

root = Path.home() / "companyos"
identity = VerifiedWalletIdentity(root).load()
example = {"chain":"solana","destination":"TEST_DESTINATION","amount":1}
injected = ProposalSourceInjector().inject(example, identity)
guard = ExecutionSourceGuard().validate(injected.get("proposal",{}), identity) if injected.get("success") else None
print(json.dumps({"success":bool(identity.get("success")),"status":"wallet_source_integration_check_complete","identity":identity,"proposal_injection":injected,"execution_guard":guard}, indent=2))
