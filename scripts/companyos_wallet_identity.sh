#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${HOME}/companyos"
SECURE="${HOME}/.companyos_secure"
RUNTIME="${HOME}/companyos_runtime"
WRAPPER="${SECURE}/multichain_signer_wrapper.sh"
IDENTITY="${RUNTIME}/wallet_identity.json"

mkdir -p "$RUNTIME"
chmod 700 "$RUNTIME"

case "${1:-sync}" in

  sync)
    RESULT="$(
      printf '%s\n' \
      '{"action":"get_public_address","chain":"solana"}' \
      | "$WRAPPER"
    )"

    JSON="$(printf '%s\n' "$RESULT" | grep '^{' | tail -1)"

    python - "$JSON" "$IDENTITY" <<'PY'
import json, sys
from pathlib import Path

data=json.loads(sys.argv[1])

if not data.get("success"):
    raise SystemExit("IDENTITY_DISCOVERY_FAILED")

address=data.get("public_address")

if not address:
    raise SystemExit("PUBLIC_ADDRESS_MISSING")

out={
    "chain":"solana",
    "public_address":address,
    "source":"secure_signer_derived",
    "private_key_exposed":False
}

p=Path(sys.argv[2])
p.write_text(json.dumps(out,indent=2)+"\n")
p.chmod(0o600)

print(json.dumps({
    "success":True,
    "status":"wallet_identity_synced",
    "chain":"solana",
    "public_address":address,
    "private_key_exposed":False
},indent=2))
PY
    ;;

  show)
    test -f "$IDENTITY" || {
      echo '{"success":false,"status":"identity_not_synced"}'
      exit 1
    }
    cat "$IDENTITY"
    ;;

  verify)
    test -f "$IDENTITY" || {
      echo '{"success":false,"status":"identity_not_synced"}'
      exit 1
    }

    CURRENT="$(
      printf '%s\n' \
      '{"action":"get_public_address","chain":"solana"}' \
      | "$WRAPPER" |
      grep '^{' |
      tail -1
    )"

    python - "$CURRENT" "$IDENTITY" <<'PY'
import json,sys

live=json.loads(sys.argv[1])
saved=json.load(open(sys.argv[2]))

ok=(
    live.get("success") is True
    and live.get("public_address")==saved.get("public_address")
)

print(json.dumps({
    "success":ok,
    "status":"wallet_identity_verified" if ok else "wallet_identity_mismatch",
    "chain":"solana",
    "public_address":saved.get("public_address")
},indent=2))

raise SystemExit(0 if ok else 1)
PY
    ;;

  *)
    echo "Usage: $0 {sync|show|verify}"
    exit 2
    ;;
esac
