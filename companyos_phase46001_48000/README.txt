CompanyOS Phase 46001-48000
NON-BROADCAST TRANSACTION LIFECYCLE

Connects the verified wallet identity into the transaction preparation path.

Adds:
- verified signer-derived wallet source
- transaction amount policy
- destination allowlist enforcement
- balance + estimated-fee reserve protection
- duplicate payment fingerprint protection
- financial kill switch enforcement
- non-broadcast transaction validation state

Flow:
CEO decision
 -> verified wallet identity
 -> source guard
 -> treasury-style transaction policy
 -> destination allowlist
 -> balance/fee reserve check
 -> duplicate payment guard
 -> non-broadcast validation

This phase does NOT auto-enable signing or broadcasting.
