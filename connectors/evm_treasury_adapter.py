#!/usr/bin/env python3
import json,sys,os
mode=sys.argv[1] if len(sys.argv)>1 else "status"
payload=json.loads(sys.argv[2]) if len(sys.argv)>2 else {}
required_env={
  "solana":["SOLANA_RPC_URL","SOLANA_SIGNER_COMMAND"],
  "evm":["EVM_RPC_URL","EVM_SIGNER_COMMAND"],
  "bitcoin":["BITCOIN_RPC_URL","BITCOIN_SIGNER_COMMAND"]
}["evm"]
missing=[k for k in required_env if not os.getenv(k,"").strip()]
if missing:
    print(json.dumps({
      "success":False,
      "status":"signer_not_configured",
      "chain":"evm",
      "missing_env":missing,
      "mode":mode
    },indent=2))
    raise SystemExit(2)

print(json.dumps({
  "success":False,
  "status":"adapter_requires_provider_specific_implementation",
  "chain":"evm",
  "mode":mode,
  "message":"Configure the RPC/provider-specific transaction builder and signer command before live broadcast."
},indent=2))
raise SystemExit(3)
