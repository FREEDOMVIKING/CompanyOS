CompanyOS Phase 48001-50000
SOLANA NON-BROADCAST SIMULATION

Purpose:
Connect the verified wallet identity to Solana RPC validation and transaction simulation
without broadcasting funds.

Adds:
- verified signer-derived Solana identity requirement
- latest blockhash check
- live wallet balance check
- non-broadcast transaction planning
- signer-assisted signed transaction simulation when serialized transaction data is returned
- simulation gate for future live-readiness review

Important:
- no broadcast is attempted
- live execution remains disabled
- a live-ready state is never auto-enabled by this phase
