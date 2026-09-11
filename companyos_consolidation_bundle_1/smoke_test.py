from companyos.canonicalexec import CanonicalExecutionGateway, ExecutionRequest
g=CanonicalExecutionGateway()
r1=g.execute(ExecutionRequest(action="internal_probe",idempotency_key="bundle1-internal"))
assert r1.accepted and not r1.transaction_broadcast_performed
r2=g.execute(ExecutionRequest(action="financial_probe",financial_action=True,idempotency_key="bundle1-financial"))
assert r2.accepted and not r2.transaction_broadcast_performed
r3=g.execute(ExecutionRequest(action="financial_probe",financial_action=True,idempotency_key="bundle1-financial"))
assert not r3.accepted and r3.status=="duplicate_rejected"
r4=g.execute(ExecutionRequest(action="approval_probe",requires_human_approval=True,idempotency_key="bundle1-approval"))
assert not r4.accepted and r4.status=="approval_required"
print("internal_request => PASS")
print("financial_dry_run => PASS")
print("duplicate_protection => PASS")
print("approval_gate => PASS")
print("no_transaction_broadcast => PASS")
print("BUNDLE1_SMOKE_TEST: PASS")
