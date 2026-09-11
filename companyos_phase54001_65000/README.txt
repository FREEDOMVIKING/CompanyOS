CompanyOS Phase 54001-65000
FINAL BOUNDED LIVE FINANCIAL INTEGRATION

This is the large final integration push for the financial execution path.

Integrated path:
CompanyOS autonomous operating runtime
 -> controlled live-readiness gate
 -> one-shot authorization
 -> verified signer-derived wallet identity
 -> treasury/amount policy
 -> destination allowlist
 -> balance + reserve checks
 -> duplicate/idempotency protection
 -> financial kill switch
 -> existing Solana multichain execution adapter
 -> signer/provider execution
 -> execution receipt
 -> receipt verification/reconciliation
 -> automatic post-execution lockout

Important operating model:
- Live execution is OFF after install.
- It requires explicit enablement through live_financial.env.
- Default bounded live limits are intentionally small.
- Allowlisting remains required by default.
- Every live attempt consumes authorization and triggers post-execution lockout.
- No unbounded autonomous spending mode is included.

Commands:
  bash ~/companyos/scripts/companyos_live_final.sh status
  bash ~/companyos/scripts/companyos_live_final.sh enable-bounded
  bash ~/companyos/scripts/companyos_live_final.sh disable

The runtime can be live-capable while still retaining strict financial boundaries.
