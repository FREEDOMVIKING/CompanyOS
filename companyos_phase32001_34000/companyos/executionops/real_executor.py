import importlib.util
import inspect
from pathlib import Path
from .capability_discovery import CapabilityDiscovery
from .receipt_store import ExecutionReceiptStore
from .verifier import ExecutionVerifier

class RealCapabilityExecutor:
    METHOD_NAMES = ("execute","run","handle","process","dispatch","invoke")

    def __init__(self, root):
        self.root = Path(root)
        self.discovery = CapabilityDiscovery(root)
        self.receipts = ExecutionReceiptStore(root)

    def _load_module(self, relpath):
        path = self.root / relpath
        spec = importlib.util.spec_from_file_location("companyos_dynamic_capability", str(path))
        if not spec or not spec.loader:
            raise RuntimeError("capability_module_load_failed")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def _call(self, mod, payload):
        for name in self.METHOD_NAMES:
            fn = getattr(mod, name, None)
            if callable(fn):
                try:
                    sig = inspect.signature(fn)
                    if len(sig.parameters) == 0:
                        return fn()
                    return fn(payload)
                except TypeError:
                    continue

        for obj_name in dir(mod):
            obj = getattr(mod, obj_name, None)
            if inspect.isclass(obj):
                try:
                    inst = obj()
                except Exception:
                    continue
                for name in self.METHOD_NAMES:
                    fn = getattr(inst, name, None)
                    if callable(fn):
                        try:
                            sig = inspect.signature(fn)
                            if len(sig.parameters) == 0:
                                return fn()
                            return fn(payload)
                        except TypeError:
                            continue

        return {"success":False,"status":"no_supported_entrypoint"}

    def execute(self, capability, payload):
        rel = self.discovery.best_for(capability)
        if not rel:
            return {
                "success": False,
                "status": "capability_missing",
                "capability": capability,
            }

        try:
            mod = self._load_module(rel)
            raw = self._call(mod, payload)
            result = raw if isinstance(raw, dict) else {"success":True,"output":raw}
        except Exception as exc:
            result = {
                "success":False,
                "status":"execution_exception",
                "error":type(exc).__name__,
                "message":str(exc),
            }

        verification = ExecutionVerifier().verify(result)
        receipt = self.receipts.append({
            "capability":capability,
            "module":rel,
            "payload":payload,
            "result":result,
            "verification":verification,
        })

        return {
            "success": bool(verification["passed"]),
            "status": "verified_execution_complete" if verification["passed"] else "execution_unverified",
            "module": rel,
            "result": result,
            "verification": verification,
            "receipt": receipt,
        }
