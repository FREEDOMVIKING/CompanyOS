#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
cd "$ROOT"

echo "===== COMPANYOS EXTERNAL ACTION COMMISSIONING ====="

# Load local environment if available.
[ ! -f "$HOME/.companyos_launch_env" ] || . "$HOME/.companyos_launch_env"

echo
echo "===== PRECHECK ====="
./scripts/companyosctl health || true

echo
echo "===== LOCATE EXTERNAL CONNECTOR IMPLEMENTATIONS ====="
find companyos -maxdepth 4 -type f \( \
  -name '*openai*' -o \
  -name '*smtp*' -o \
  -name '*deploy*' -o \
  -name '*vercel*' -o \
  -name '*solana*' -o \
  -name '*connector*' \
\) | sort | sed -n '1,160p'

echo
echo "===== NON-DESTRUCTIVE CONNECTOR TESTS ====="
python - <<'PY'
from __future__ import annotations
import importlib
import json
import os
import socket
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path.home() / "companyos"
sys.path.insert(0, str(ROOT))

results = {}

def add(name, ok, **extra):
    results[name] = {"ok": bool(ok), **extra}

# 1) OpenAI: verify key presence and a minimal authenticated API call.
key = os.getenv("OPENAI_API_KEY", "")
if not key:
    add("openai", False, reason="OPENAI_API_KEY_missing")
else:
    try:
        req = Request(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            method="GET",
        )
        with urlopen(req, timeout=15) as r:
            add("openai", r.status == 200, http_status=r.status)
    except Exception as exc:
        add("openai", False, reason=f"{type(exc).__name__}:{exc}")

# 2) SMTP: test TCP reachability + optional authenticated handshake, no email sent.
host = os.getenv("SMTP_HOST", "")
port = int(os.getenv("SMTP_PORT", "587") or 587)
user = os.getenv("SMTP_USERNAME", "")
pwd = os.getenv("SMTP_PASSWORD", "")
if not host:
    add("smtp", False, reason="SMTP_HOST_missing")
else:
    try:
        import smtplib
        with smtplib.SMTP(host, port, timeout=15) as s:
            s.ehlo()
            if port == 587:
                s.starttls()
                s.ehlo()
            auth_ok = None
            if user and pwd:
                s.login(user, pwd)
                auth_ok = True
            add("smtp", True, reachable=True, authenticated=auth_ok)
    except Exception as exc:
        add("smtp", False, reason=f"{type(exc).__name__}:{exc}")

# 3) GitHub: use git transport against configured origin, read-only.
try:
    import subprocess
    p = subprocess.run(
        ["git", "ls-remote", "--exit-code", "origin", "HEAD"],
        cwd=ROOT, text=True, capture_output=True, timeout=20
    )
    add("github", p.returncode == 0, stdout=p.stdout.strip()[-200:], stderr=p.stderr.strip()[-200:])
except Exception as exc:
    add("github", False, reason=f"{type(exc).__name__}:{exc}")

# 4) Hosting/Vercel: verify token with read-only API call, no deployment.
vercel = os.getenv("VERCEL_TOKEN", "")
if not vercel:
    add("vercel", False, reason="VERCEL_TOKEN_missing")
else:
    try:
        req = Request(
            "https://api.vercel.com/v2/user",
            headers={"Authorization": f"Bearer {vercel}"},
            method="GET",
        )
        with urlopen(req, timeout=15) as r:
            add("vercel", r.status == 200, http_status=r.status)
    except Exception as exc:
        add("vercel", False, reason=f"{type(exc).__name__}:{exc}")

# 5) Solana RPC: read-only JSON-RPC getHealth and getBalance if public key can be derived.
rpc = os.getenv("SOLANA_RPC_URL", "")
if not rpc:
    add("solana_rpc", False, reason="SOLANA_RPC_URL_missing")
else:
    try:
        payload = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getHealth"
        }).encode()
        req = Request(rpc, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(req, timeout=15) as r:
            body = json.loads(r.read().decode())
            ok = body.get("result") == "ok" and "error" not in body
            add("solana_rpc", ok, response=body)
    except Exception as exc:
        add("solana_rpc", False, reason=f"{type(exc).__name__}:{exc}")

# 6) Solana signer: local-only import/parse test. No transaction constructed or signed.
priv = os.getenv("SOLANA_PRIVATE_KEY", "")
if not priv:
    add("solana_signer", False, reason="SOLANA_PRIVATE_KEY_missing")
else:
    parsed = False
    details = []
    # Try common installed libraries without printing the key.
    try:
        import base58
        raw = base58.b58decode(priv)
        if len(raw) in (32, 64):
            parsed = True
            details.append(f"base58_len={len(raw)}")
    except Exception:
        pass
    if not parsed:
        try:
            import base64
            raw = base64.b64decode(priv)
            if len(raw) in (32, 64):
                parsed = True
                details.append(f"base64_len={len(raw)}")
        except Exception:
            pass
    add("solana_signer", parsed, details=details)

print(json.dumps(results, indent=2, sort_keys=True))

failed = [k for k,v in results.items() if not v.get("ok")]
print()
print("===== SUMMARY =====")
print("passed:", [k for k,v in results.items() if v.get("ok")])
print("failed:", failed)
print("external_commissioning_pass:", not failed)
PY

echo
echo "===== RECENT EXTERNAL-ACTION LOG SIGNALS ====="
grep -RhiE 'deploy|smtp|email|github|solana|openai|external action|live_url|transaction' \
  .companyos_runtime/*.log 2>/dev/null | tail -n 80 || true

echo
echo "COMPANYOS_EXTERNAL_ACTION_COMMISSIONING=COMPLETE"
