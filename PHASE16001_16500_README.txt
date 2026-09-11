CompanyOS Phase 16001-16500
REAL CAPABILITY EXECUTION LAYER

What this closes:
- Worker jobs can now delegate to configured real provider endpoints.
- Research jobs can send structured live research requests.
- Reasoning/product/growth/customer-success/operations jobs can call a configured reasoning provider.
- Finance is read-only unless a separately governed action is approved.
- Every capability execution writes a durable receipt digest.
- Recent capability outcomes feed persistent runtime memory.
- Consequential external actions remain approval-gated.

IMPORTANT:
This package does NOT invent credentials or provider endpoints.
Without configured URLs/API keys, jobs safely run in internal fallback mode.

CHECK:
bash ~/companyos/scripts/companyos_capabilities.sh status

VERIFY:
bash ~/companyos/scripts/companyos_capabilities.sh verify
