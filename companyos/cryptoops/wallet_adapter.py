import importlib.util
import inspect
from pathlib import Path

class ExistingWalletAdapter:
    """
    Adapter around an existing CompanyOS wallet implementation.

    This class never reads or stores private key material itself.
    It imports the discovered wallet module and calls supported public methods.
    """

    BALANCE_METHODS = ("get_balance","balance","get_wallet_balance")
    ADDRESS_METHODS = ("get_address","address","get_wallet_address")
    SEND_METHODS = ("send_transaction","transfer","send","execute_transfer")

    def __init__(self, wallet_file):
        self.wallet_file = Path(wallet_file)
        self.module = self._load_module(self.wallet_file)
        self.wallet = self._instantiate(self.module)

    def _load_module(self, path):
        spec = importlib.util.spec_from_file_location("companyos_existing_wallet", str(path))
        if not spec or not spec.loader:
            raise RuntimeError("wallet_module_load_failed")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def _instantiate(self, mod):
        preferred = ("WalletPort","WalletManager","CryptoWallet","Wallet","WalletAdapter")
        for name in preferred:
            cls = getattr(mod, name, None)
            if inspect.isclass(cls):
                try:
                    return cls()
                except TypeError:
                    continue
        return mod

    def _find_callable(self, names):
        for name in names:
            fn = getattr(self.wallet, name, None)
            if callable(fn):
                return fn
        return None

    def get_address(self):
        fn = self._find_callable(self.ADDRESS_METHODS)
        if fn:
            value = fn()
            return {"success": True, "address": value}
        for name in ("wallet_address","public_key","address"):
            value = getattr(self.wallet, name, None)
            if value:
                return {"success": True, "address": str(value)}
        return {"success": False, "error": "wallet_address_method_not_found"}

    def get_balance(self):
        fn = self._find_callable(self.BALANCE_METHODS)
        if not fn:
            return {"success": False, "error": "wallet_balance_method_not_found"}
        value = fn()
        if isinstance(value, dict):
            return value
        return {"success": True, "balance": value}

    def execute_transfer(self, *, amount, destination, memo="", idempotency_key=None):
        fn = self._find_callable(self.SEND_METHODS)
        if not fn:
            return {"success": False, "error": "wallet_send_method_not_found"}

        attempts = [
            {"amount":amount, "destination":destination, "memo":memo, "idempotency_key":idempotency_key},
            {"amount":amount, "to":destination, "memo":memo},
            {"amount":amount, "address":destination},
        ]
        last = None
        for kwargs in attempts:
            try:
                sig = inspect.signature(fn)
                accepted = {k:v for k,v in kwargs.items() if k in sig.parameters}
                if not accepted and sig.parameters:
                    continue
                result = fn(**accepted)
                return result if isinstance(result, dict) else {"success": True, "result": result}
            except Exception as exc:
                last = exc
        return {"success": False, "error": type(last).__name__ if last else "wallet_send_failed", "message": str(last) if last else ""}

    def list_transactions(self, limit=100):
        fn = getattr(self.wallet, "list_transactions", None)
        if callable(fn):
            value = fn(limit=limit)
            return value if isinstance(value, list) else []
        return []
