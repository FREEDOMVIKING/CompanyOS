#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos.cryptoops import WalletDiscovery, CryptoAllowlist, CryptoOpsStatus

root = Path(tempfile.mkdtemp())
(root / "wallet_port.py").write_text(
    "class WalletPort:\\n"
    "    wallet_address='TEST_PUBLIC_ADDRESS'\\n"
    "    def get_balance(self): return {'success':True,'balance':1000}\\n"
    "    def send_transaction(self, amount, destination): return {'success':True,'tx_id':'test'}\\n"
)

scan = WalletDiscovery(root).scan()
assert scan and scan[0]["name"] == "wallet_port.py"

allow = CryptoAllowlist(root)
allow.save(["addr1","addr2","addr1"])
assert allow.load() == {"addr1","addr2"}

s = CryptoOpsStatus().status()
assert s["private_keys_embedded"] is False
assert s["live_transfer_enabled_by_default"] is False

print(json.dumps({
    "success": True,
    "status": "phase23001_24000_verification_passed",
    "cycle_status": "phase24000_existing_crypto_wallet_connector_ready",
    "live_transfer_enabled_by_default": False
}, indent=2))
