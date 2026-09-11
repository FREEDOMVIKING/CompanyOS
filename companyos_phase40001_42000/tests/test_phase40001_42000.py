from pathlib import Path
import tempfile
from companyos.walletautobind import ExistingWalletLocator, WalletBindingWriter

def test_locator_and_binding():
    root = Path(tempfile.mkdtemp())
    (root/"wallet_port.py").write_text(
        "wallet_address='X'\n"
        "def sign_transaction(x): return x\n"
        "def send_transaction(x): return x\n"
        "SOLANA='yes'\n"
    )
    best = ExistingWalletLocator(root).best()
    assert best is not None
    out = WalletBindingWriter(root).write(best)
    assert out["success"] is True
    assert out["binding"]["contains_private_key_material"] is False
