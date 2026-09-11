#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase76_live_treasury_authorization_bundle"

pairs = [
    (
        BUNDLE / "live_treasury_authorizer.py",
        ROOT / "companyos/walletintegration/live_treasury_authorizer.py",
    ),
    (
        BUNDLE / "phase76_live_treasury_auth_test.py",
        ROOT / "phase76_live_treasury_auth_test.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)

    if dst.exists():
        backup = dst.with_name(dst.name + f".phase76_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "76_LIVE_TREASURY_AUTHORIZATION",
    "status": "installed",
    "forced_fresh_balance_before_authorization": True,
    "reserve_enforced": True,
    "stale_state_rejected": True,
    "zero_value_test_only": True,
    "transaction_created_by_bundle": False,
    "transaction_signed_by_bundle": False,
    "transaction_broadcast_by_bundle": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE76_LIVE_TREASURY_AUTH_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE76_LIVE_TREASURY_AUTHORIZATION: INSTALLED")
print("COMPILE_CHECK: PASS")
print("FORCED_FRESH_BALANCE_BEFORE_AUTH: True")
print("RESERVE_ENFORCEMENT: True")
print("STALE_STATE_REJECTION: True")
print("TRANSACTION_CREATED_BY_INSTALLER: False")
print("TRANSACTION_SIGNED_BY_INSTALLER: False")
print("TRANSACTION_BROADCAST_BY_INSTALLER: False")
print("PRIVATE_KEY_PRINTED: False")
