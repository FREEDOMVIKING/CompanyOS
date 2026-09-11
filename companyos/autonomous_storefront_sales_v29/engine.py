
import hashlib
import json
import os
import secrets
import tempfile
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
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True, default=str)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

def append_jsonl(path, row):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True, default=str) + "\n")

class AutonomousStorefrontSalesV29:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/autonomous_storefront_sales_v29_1150001_1200000"
        self.records = self.home / "storefront_sales_records_v29"
        self.products_root = self.home / "generated_products_v28"
        self.orders_file = self.records / "orders.json"
        self.entitlements_file = self.records / "download_entitlements.json"
        self.fulfillment_file = self.records / "fulfillment_queue.json"
        self.approvals_file = self.records / "storefront_approval_queue.json"
        for p in (self.live, self.runtime, self.records):
            p.mkdir(parents=True, exist_ok=True)

    def catalog(self):
        products = []
        if not self.products_root.exists():
            return products
        for product_dir in sorted(self.products_root.iterdir()):
            if not product_dir.is_dir():
                continue
            versions = [p for p in product_dir.iterdir() if p.is_dir()]
            if not versions:
                continue
            versions.sort(key=lambda p: p.name, reverse=True)
            workspace = versions[0]
            manifest = read_json(workspace / "product_manifest.json", {})
            if not manifest:
                continue
            products.append({
                "product_id": manifest.get("product_id", product_dir.name),
                "name": manifest.get("name", product_dir.name),
                "version": manifest.get("version", workspace.name),
                "product_type": manifest.get("product_type"),
                "quality_score": manifest.get("quality_score", 0),
                "state": manifest.get("state"),
                "price_usd": manifest.get("pricing", {}).get("recommended", 0),
                "pricing": manifest.get("pricing", {}),
                "workspace": str(workspace),
                "quick_start_guide": str(workspace / "quick_start_guide.html"),
                "editable_tool": str(workspace / "editable_tool.csv"),
                "external_publish_approved": bool(
                    manifest.get("external_publish_approved", False)
                ),
            })
        return products

    def load_orders(self):
        return read_json(self.orders_file, {"orders": []}).get("orders", [])

    def save_orders(self, orders):
        write_json(self.orders_file, {"orders": orders, "updated_at": now()})

    def create_order(self, product_id, customer_ref=None):
        catalog = {p["product_id"]: p for p in self.catalog()}
        product = catalog.get(product_id)
        if not product:
            raise ValueError("product_not_found")

        order_id = "ord_" + secrets.token_hex(8)
        payment_reference = "pay_" + secrets.token_hex(10)
        order = {
            "order_id": order_id,
            "product_id": product_id,
            "product_name": product["name"],
            "version": product["version"],
            "amount_usd": product["price_usd"],
            "currency": "USD_REFERENCE",
            "payment_method": "CRYPTO_BRIDGE",
            "payment_reference": payment_reference,
            "payment_status": "PENDING_VERIFIED_CONFIRMATION",
            "order_status": "PENDING_PAYMENT",
            "customer_ref_hash": (
                hashlib.sha256(str(customer_ref).encode()).hexdigest()
                if customer_ref else None
            ),
            "license_key": None,
            "download_entitlement_created": False,
            "created_at": now(),
            "updated_at": now(),
        }
        orders = self.load_orders()
        orders.append(order)
        self.save_orders(orders)
        append_jsonl(self.records / "order_audit.jsonl", {
            "ts": now(),
            "event": "order_created",
            "order_id": order_id,
            "product_id": product_id,
        })
        return order

    def mark_paid(self, order_id, verified_receipt):
        if not verified_receipt or not verified_receipt.get("verified"):
            raise ValueError("verified_receipt_required")

        orders = self.load_orders()
        order = next((x for x in orders if x["order_id"] == order_id), None)
        if not order:
            raise ValueError("order_not_found")

        order["payment_status"] = "PAID_VERIFIED"
        order["order_status"] = "READY_FOR_FULFILLMENT"
        order["verified_receipt"] = {
            "transaction_id": verified_receipt.get("transaction_id"),
            "chain": verified_receipt.get("chain"),
            "verified": True,
        }
        order["license_key"] = "COS-" + secrets.token_hex(12).upper()
        order["updated_at"] = now()
        self.save_orders(orders)

        entitlements = read_json(self.entitlements_file, {"entitlements": []})
        entitlements["entitlements"].append({
            "order_id": order["order_id"],
            "product_id": order["product_id"],
            "version": order["version"],
            "license_key": order["license_key"],
            "status": "ACTIVE",
            "created_at": now(),
        })
        write_json(self.entitlements_file, entitlements)

        queue = read_json(self.fulfillment_file, {"items": []})
        queue["items"].append({
            "order_id": order["order_id"],
            "product_id": order["product_id"],
            "status": "READY_FOR_LOCAL_DELIVERY",
            "automatic_email_delivery": False,
            "created_at": now(),
        })
        write_json(self.fulfillment_file, queue)

        order["download_entitlement_created"] = True
        self.save_orders(orders)
        return order

    def analytics(self, catalog, orders):
        paid = [x for x in orders if x.get("payment_status") == "PAID_VERIFIED"]
        pending = [x for x in orders if x.get("payment_status") != "PAID_VERIFIED"]
        revenue = sum(float(x.get("amount_usd", 0) or 0) for x in paid)
        conversion = round(len(paid) / len(orders) * 100, 2) if orders else 0.0
        return {
            "products_total": len(catalog),
            "orders_total": len(orders),
            "orders_paid": len(paid),
            "orders_pending": len(pending),
            "verified_revenue_usd": round(revenue, 2),
            "order_conversion_percent": conversion,
        }

    def approval_queue(self, catalog):
        return [{
            "approval_id": f"publish-{p['product_id']}-{p['version']}",
            "type": "STOREFRONT_PUBLICATION",
            "product_id": p["product_id"],
            "name": p["name"],
            "version": p["version"],
            "quality_score": p["quality_score"],
            "status": (
                "APPROVED"
                if p["external_publish_approved"]
                else "REVIEW_REQUIRED"
            ),
        } for p in catalog]

    def run_cycle(self):
        catalog = self.catalog()
        orders = self.load_orders()
        approvals = self.approval_queue(catalog)
        analytics = self.analytics(catalog, orders)

        state = {
            "status": "autonomous_storefront_sales_ready",
            "catalog": catalog,
            "approval_queue": approvals,
            "analytics": analytics,
            "public_storefront_enabled": False,
            "automatic_payment_confirmation_enabled": False,
            "automatic_customer_email_enabled": False,
            "local_checkout_enabled": True,
            "crypto_bridge_status_url": "http://127.0.0.1:8771/api/status",
            "dashboard_url": "http://127.0.0.1:8791",
            "updated_at": now(),
        }

        write_json(self.runtime / "storefront_sales_state.json", state)
        write_json(self.live / "autonomous_storefront_sales_v29_live.json", state)
        write_json(self.approvals_file, {
            "approvals": approvals,
            "updated_at": now(),
        })
        append_jsonl(self.live / "full_autonomy_journal.jsonl", {
            "ts": now(),
            "event": "autonomous_storefront_sales_v29_cycle",
            "event_type": "autonomous_storefront_sales_v29_cycle",
            "state": {
                "products_total": analytics["products_total"],
                "orders_total": analytics["orders_total"],
                "orders_paid": analytics["orders_paid"],
            },
        })
        return state
