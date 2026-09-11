import importlib
import inspect
import json
import os
import re
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

def now():
    return datetime.now(timezone.utc).isoformat()

def read_json(path, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default

def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True, default=str)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def append_jsonl(path, row):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True, default=str) + "\n")

def looks_like_solana_address(value):
    value = str(value or "").strip()
    return bool(re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", value))

class ExistingWalletAdapter:
    MODULE_CANDIDATES = [
        "companyos.paymentops.payment_orchestrator",
        "companyos.walletintegration.status",
        "companyos.walletintegration.solana_rpc_preflight",
        "companyos.walletintegration.solana_confirmation_tracker",
        "companyos.walletintegration.solana_execution_gate",
        "companyos.cryptoops.wallet_discovery",
    ]

    PUBLIC_ENV_KEYS = [
        "COMPANYOS_WALLET_ADDRESS",
        "SOLANA_WALLET_ADDRESS",
        "PHANTOM_WALLET_ADDRESS",
        "WALLET_ADDRESS",
    ]

    def __init__(self, home):
        self.home = Path(home)
        self.loaded = {}
        self.errors = {}

    def discover_modules(self):
        for name in self.MODULE_CANDIDATES:
            try:
                self.loaded[name] = importlib.import_module(name)
            except Exception as exc:
                self.errors[name] = str(exc)
        return {
            "loaded": sorted(self.loaded),
            "errors": self.errors,
        }

    def public_wallet_address(self):
        for key in self.PUBLIC_ENV_KEYS:
            value = os.getenv(key)
            if looks_like_solana_address(value):
                return value, f"env:{key}"

        safe_files = [
            self.home / "ceo_memory" / "treasury_wallet.json",
            self.home / "ceo_memory" / "payment_registration.json",
            self.home / ".companyos_runtime" / "wallet_status.json",
            self.home / "companyos_runtime" / "wallet_status.json",
        ]
        for path in safe_files:
            data = read_json(path, {})
            for key in ("wallet_address", "public_key", "public_address", "address"):
                value = data.get(key)
                if looks_like_solana_address(value):
                    return value, str(path)

        for module in self.loaded.values():
            for attr_name in ("get_wallet_address", "wallet_address", "public_wallet_address"):
                try:
                    attr = getattr(module, attr_name, None)
                    value = attr() if callable(attr) and len(inspect.signature(attr).parameters) == 0 else attr
                    if looks_like_solana_address(value):
                        return value, f"module:{module.__name__}.{attr_name}"
                except Exception:
                    pass
        return None, None

    def confirmation_capability(self):
        names = []
        for module in self.loaded.values():
            for attr_name in dir(module):
                low = attr_name.lower()
                if any(token in low for token in ("confirm", "payment", "transaction", "signature", "receipt")):
                    attr = getattr(module, attr_name, None)
                    if callable(attr):
                        names.append(f"{module.__name__}.{attr_name}")
        return sorted(set(names))

    def verify_payment(self, invoice):
        """
        Conservative adapter:
        Calls only clearly named, low-arity verification functions.
        Any ambiguous or incompatible result stays unverified.
        """
        candidates = []
        for module in self.loaded.values():
            for attr_name in (
                "verify_payment",
                "confirm_payment",
                "check_payment",
                "verify_transaction",
                "confirm_transaction",
                "lookup_payment",
            ):
                fn = getattr(module, attr_name, None)
                if callable(fn):
                    candidates.append((module.__name__, attr_name, fn))

        for module_name, attr_name, fn in candidates:
            try:
                params = list(inspect.signature(fn).parameters)
                kwargs = {
                    "wallet_address": invoice.get("wallet_address"),
                    "amount": invoice.get("amount"),
                    "amount_usd": invoice.get("amount_usd"),
                    "memo": invoice.get("memo"),
                    "invoice_id": invoice.get("invoice_id"),
                    "created_at": invoice.get("created_at"),
                    "product_id": invoice.get("product_id"),
                    "order_id": invoice.get("order_id"),
                }
                call_kwargs = {k: v for k, v in kwargs.items() if k in params}
                if len(call_kwargs) != len(params):
                    continue
                result = fn(**call_kwargs)
                parsed = self._normalize_result(result)
                if parsed["verified"]:
                    parsed["adapter"] = f"{module_name}.{attr_name}"
                    return parsed
            except Exception:
                continue

        return {
            "verified": False,
            "status": "AWAITING_VERIFIED_PAYMENT",
            "transaction_id": None,
            "adapter": None,
        }

    def _normalize_result(self, result):
        if isinstance(result, bool):
            return {
                "verified": result,
                "status": "PAID" if result else "AWAITING_VERIFIED_PAYMENT",
                "transaction_id": None,
            }
        if isinstance(result, dict):
            verified = bool(
                result.get("verified")
                or result.get("confirmed")
                or result.get("paid")
                or str(result.get("status", "")).upper() in {"PAID", "CONFIRMED", "FINALIZED"}
            )
            return {
                "verified": verified,
                "status": "PAID" if verified else "AWAITING_VERIFIED_PAYMENT",
                "transaction_id": result.get("transaction_id") or result.get("signature") or result.get("txid"),
            }
        return {
            "verified": False,
            "status": "AWAITING_VERIFIED_PAYMENT",
            "transaction_id": None,
        }

class CryptoPaymentBridgeV9:
    def __init__(self, home):
        self.home = Path(home)
        self.runtime = self.home / "companyos_runtime" / "crypto_payment_bridge_v9_220001_250000"
        self.live = self.home / ".companyos_runtime"
        self.storefront_runtime = self.home / "companyos_runtime" / "storefront_sales_v8_190001_220000"
        self.fulfillment = self.home / "storefront_v8_fulfillment"
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.live.mkdir(parents=True, exist_ok=True)
        self.adapter = ExistingWalletAdapter(home)
        self.adapter.discover_modules()

    def invoices(self):
        return read_json(self.runtime / "invoices.json", {"invoices": []})

    def orders(self):
        return read_json(self.storefront_runtime / "orders.json", {"orders": []})

    def catalog(self):
        return read_json(self.storefront_runtime / "catalog.json", {"products": []})

    def create_invoice(self, product_id, email):
        product = next((p for p in self.catalog().get("products", []) if p.get("product_id") == product_id), None)
        if not product:
            return {"ok": False, "error": "unknown_product"}, 404

        wallet_address, source = self.adapter.public_wallet_address()
        if not wallet_address:
            return {"ok": False, "error": "public_wallet_address_not_available"}, 409

        amount_usd = product.get("pricing", {}).get("recommended", 0)
        invoice_id = str(uuid.uuid4())
        order_id = str(uuid.uuid4())
        memo = f"COMPANYOS-{invoice_id[:12]}"

        invoice = {
            "invoice_id": invoice_id,
            "order_id": order_id,
            "product_id": product_id,
            "product_name": product.get("name"),
            "email": email,
            "chain": "solana",
            "asset": "USDC_OR_SOL_CONFIGURED_EXTERNALLY",
            "amount_usd": amount_usd,
            "amount": None,
            "wallet_address": wallet_address,
            "wallet_address_source": source,
            "memo": memo,
            "status": "AWAITING_VERIFIED_PAYMENT",
            "transaction_id": None,
            "fulfillment_package": product.get("fulfillment_package"),
            "created_at": now(),
            "updated_at": now(),
        }

        data = self.invoices()
        data["invoices"].append(invoice)
        write_json(self.runtime / "invoices.json", data)

        ledger = self.orders()
        ledger["orders"].append({
            "order_id": order_id,
            "invoice_id": invoice_id,
            "product_id": product_id,
            "email": email,
            "amount_usd": amount_usd,
            "status": "CRYPTO_PAYMENT_PENDING",
            "fulfillment_package": product.get("fulfillment_package"),
            "created_at": now(),
        })
        write_json(self.storefront_runtime / "orders.json", ledger)
        self.update_analytics()
        return {"ok": True, "invoice": invoice}, 201

    def check_invoices(self):
        data = self.invoices()
        changed = 0
        for invoice in data["invoices"]:
            if invoice.get("status") == "PAID":
                continue
            result = self.adapter.verify_payment(invoice)
            invoice["last_check_at"] = now()
            if result.get("verified"):
                invoice["status"] = "PAID"
                invoice["transaction_id"] = result.get("transaction_id")
                invoice["verification_adapter"] = result.get("adapter")
                invoice["paid_at"] = now()
                invoice["updated_at"] = now()
                self._mark_order_paid(invoice)
                self._write_fulfillment_record(invoice)
                changed += 1
        write_json(self.runtime / "invoices.json", data)
        self.update_analytics()
        return {"checked": len(data["invoices"]), "newly_paid": changed}

    def _mark_order_paid(self, invoice):
        ledger = self.orders()
        for order in ledger["orders"]:
            if order.get("order_id") == invoice.get("order_id"):
                order["status"] = "PAID"
                order["transaction_id"] = invoice.get("transaction_id")
                order["paid_at"] = now()
        write_json(self.storefront_runtime / "orders.json", ledger)

    def _write_fulfillment_record(self, invoice):
        record = {
            "order_id": invoice["order_id"],
            "invoice_id": invoice["invoice_id"],
            "product_id": invoice["product_id"],
            "email": invoice["email"],
            "fulfillment_package": invoice.get("fulfillment_package"),
            "status": "READY_FOR_DELIVERY",
            "delivery_sent": False,
            "created_at": now(),
        }
        append_jsonl(self.runtime / "fulfillment_queue.jsonl", record)

    def update_analytics(self):
        orders = self.orders().get("orders", [])
        paid = [o for o in orders if o.get("status") == "PAID"]
        analytics = {
            "orders_total": len(orders),
            "orders_paid": len(paid),
            "revenue_usd": round(sum(float(o.get("amount_usd", 0) or 0) for o in paid), 2),
            "crypto_invoices_total": len(self.invoices().get("invoices", [])),
            "updated_at": now(),
        }
        write_json(self.storefront_runtime / "revenue_analytics.json", analytics)
        write_json(self.runtime / "revenue_analytics.json", analytics)
        return analytics

    def status(self):
        wallet_address, wallet_source = self.adapter.public_wallet_address()
        modules = self.adapter.discover_modules()
        capability = self.adapter.confirmation_capability()
        state = {
            "status": "crypto_bridge_ready" if wallet_address else "wallet_public_address_required",
            "wallet_public_address_loaded": bool(wallet_address),
            "wallet_public_address_masked": (
                f"{wallet_address[:5]}...{wallet_address[-5:]}" if wallet_address else None
            ),
            "wallet_source": wallet_source,
            "private_key_displayed": False,
            "loaded_modules": modules["loaded"],
            "confirmation_adapter_candidates": capability,
            "verified_confirmation_adapter_available": bool(capability),
            "invoices": len(self.invoices().get("invoices", [])),
            "analytics": self.update_analytics(),
            "updated_at": now(),
        }
        write_json(self.live / "crypto_payment_bridge_v9_live.json", state)
        return state

    def run_cycle(self):
        result = self.check_invoices()
        state = self.status()
        state["last_check"] = result
        write_json(self.live / "crypto_payment_bridge_v9_live.json", state)
        append_jsonl(self.live / "full_autonomy_journal.jsonl", {
            "ts": now(),
            "event": "crypto_payment_bridge_v9_cycle",
            "event_type": "crypto_payment_bridge_v9_cycle",
            "state": state,
        })
        return state
