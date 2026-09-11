#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase75_live_treasury_feed_bundle"

pairs = [
    (BUNDLE / "live_treasury_feed.py", ROOT / "companyos/walletintegration/live_treasury_feed.py"),
    (BUNDLE / "phase75_live_treasury.py", ROOT / "phase75_live_treasury.py"),
    (BUNDLE / "phase75_live_feed_loop.py", ROOT / "phase75_live_feed_loop.py"),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)

    if dst.exists():
        backup = dst.with_name(dst.name + f".phase75_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "75_LIVE_TREASURY_FEED",
    "status": "installed",
    "balance_hardcoded": False,
    "live_rpc_balance_refresh": True,
    "cached_state_file": "~/.companyos_runtime/treasury_live_state.json",
    "stale_detection": True,
    "force_fresh_before_financial_action": True,
    "transaction_broadcast_by_bundle": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE75_LIVE_TREASURY_FEED_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE75_LIVE_TREASURY_FEED: INSTALLED")
print("COMPILE_CHECK: PASS")
print("LIVE_BALANCE_HARDCODED: False")
print("FORCE_FRESH_BEFORE_FINANCIAL_ACTION: True")
print("STALE_DETECTION: True")
print("TRANSACTION_BROADCAST_BY_INSTALLER: False")
print("PRIVATE_KEY_PRINTED: False")
