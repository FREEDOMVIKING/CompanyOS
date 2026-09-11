from companyos.cryptoops import CryptoAllowlist, CryptoOpsStatus
import tempfile
from pathlib import Path

def test_allowlist():
    root = Path(tempfile.mkdtemp())
    a = CryptoAllowlist(root)
    a.save(["x","y","x"])
    assert a.load() == {"x","y"}

def test_status_safe():
    s = CryptoOpsStatus().status()
    assert s["private_keys_embedded"] is False
    assert s["live_transfer_enabled_by_default"] is False
