CompanyOS Phase 45001-46000
VERIFIED WALLET SOURCE INTEGRATION

Uses the verified public Solana identity derived from the secure signer as the authoritative source address.

Adds:
- verified identity loading
- automatic proposal source injection
- source mismatch rejection before execution
- placeholder/test source rejection

Safety:
- no private keys are read or copied
- treasury, preflight, kill-switch, idempotency, and receipt verification remain in place
- live execution remains disabled by default
