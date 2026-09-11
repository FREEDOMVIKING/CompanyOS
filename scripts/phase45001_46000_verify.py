#!/usr/bin/env python3
import json
from companyos.walletsource import ProposalSourceInjector, ExecutionSourceGuard, WalletSourceStatus
identity={"success":True,"public_address":"SOL_TEST_ADDRESS"}
inj=ProposalSourceInjector().inject({"chain":"solana"}, identity)
assert inj["proposal"]["source"]=="SOL_TEST_ADDRESS"
assert ProposalSourceInjector().inject({"source":"WRONG"}, identity)["status"]=="proposal_source_mismatch"
assert ExecutionSourceGuard().validate({"source":"SOL_TEST_ADDRESS"}, identity)["allowed"] is True
assert ExecutionSourceGuard().validate({"source":"WRONG"}, identity)["allowed"] is False
assert WalletSourceStatus().status()["live_execution_auto_enabled"] is False
print(json.dumps({"success":True,"status":"phase45001_46000_verification_passed","cycle_status":"phase46000_verified_wallet_source_integration_ready"}, indent=2))
