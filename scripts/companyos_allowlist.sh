#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
ALLOWFILE="$ROOT/companyos_runtime/financial_allowlist.json"

cmd="${1:-status}"
arg="${2:-}"

case "$cmd" in
  status)
    python - "$ALLOWFILE" <<'PY'
import json, sys
from pathlib import Path

p = Path(sys.argv[1])
data = json.loads(p.read_text()) if p.exists() else {
    "version": 1,
    "addresses": [],
    "default_deny": True
}

print(json.dumps({
    "success": True,
    "status": "allowlist_status",
    "count": len(data.get("addresses", [])),
    "default_deny": bool(data.get("default_deny", True)),
    "addresses": data.get("addresses", [])
}, indent=2))
PY
    ;;

  add)
    [ -n "$arg" ] || {
      echo "Usage: $0 add SOLANA_ADDRESS"
      exit 1
    }

    python - "$ALLOWFILE" "$arg" <<'PY'
import json, sys
from pathlib import Path

p = Path(sys.argv[1])
addr = sys.argv[2].strip()

data = json.loads(p.read_text()) if p.exists() else {
    "version": 1,
    "addresses": [],
    "default_deny": True
}

addresses = data.setdefault("addresses", [])

if addr not in addresses:
    addresses.append(addr)

data["default_deny"] = True

p.write_text(json.dumps(data, indent=2) + "\n")

print(json.dumps({
    "success": True,
    "status": "allowlist_address_added",
    "address": addr,
    "count": len(addresses)
}, indent=2))
PY
    ;;

  remove)
    [ -n "$arg" ] || {
      echo "Usage: $0 remove SOLANA_ADDRESS"
      exit 1
    }

    python - "$ALLOWFILE" "$arg" <<'PY'
import json, sys
from pathlib import Path

p = Path(sys.argv[1])
addr = sys.argv[2].strip()

data = json.loads(p.read_text()) if p.exists() else {
    "version": 1,
    "addresses": [],
    "default_deny": True
}

addresses = data.setdefault("addresses", [])

if addr in addresses:
    addresses.remove(addr)

p.write_text(json.dumps(data, indent=2) + "\n")

print(json.dumps({
    "success": True,
    "status": "allowlist_address_removed",
    "address": addr,
    "count": len(addresses)
}, indent=2))
PY
    ;;

  check)
    [ -n "$arg" ] || {
      echo "Usage: $0 check SOLANA_ADDRESS"
      exit 1
    }

    python - "$ALLOWFILE" "$arg" <<'PY'
import json, sys
from pathlib import Path

p = Path(sys.argv[1])
addr = sys.argv[2].strip()

data = json.loads(p.read_text()) if p.exists() else {
    "addresses": [],
    "default_deny": True
}

allowed = addr in data.get("addresses", [])

print(json.dumps({
    "success": True,
    "status": "destination_allowed" if allowed else "destination_denied",
    "address": addr,
    "allowed": allowed,
    "default_deny": bool(data.get("default_deny", True))
}, indent=2))

raise SystemExit(0 if allowed else 2)
PY
    ;;

  *)
    echo "Usage: $0 {status|add|remove|check} [SOLANA_ADDRESS]"
    exit 1
    ;;
esac
