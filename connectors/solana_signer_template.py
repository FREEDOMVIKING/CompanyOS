#!/usr/bin/env python3
"""
Template contract for the isolated signer.

stdin JSON:
{
  "action": "build_and_sign_sol_transfer",
  "proposal_id": "...",
  "source": "...",
  "destination": "...",
  "lamports": 123,
  "recent_blockhash": "..."
}

stdout JSON expected:
{
  "signed_transaction_base64": "..."
}

Replace this template with a signer implementation backed by your dedicated
treasury key storage. Do not commit secrets or seed phrases to the repo.
"""
import json,sys
req=json.load(sys.stdin)
print(json.dumps({
  "success":False,
  "status":"signer_template_only",
  "received_action":req.get("action"),
  "message":"Configure SOLANA_SIGNER_COMMAND to an isolated signer implementation."
}))
raise SystemExit(2)
