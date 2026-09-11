import json
import os
import re
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

def now():
    return datetime.now(timezone.utc).isoformat()

def slugify(value):
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-") or "product"

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

class StorefrontSalesEngineV8:
    def __init__(self, home):
        self.home = Path(home)
        self.products_root = self.home / "generated_products_v7"
        self.runtime = self.home / "companyos_runtime" / "storefront_sales_v8_190001_220000"
        self.live = self.home / ".companyos_runtime"
        self.storefront = self.home / "storefront_v8"
        self.fulfillment = self.home / "storefront_v8_fulfillment"
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.live.mkdir(parents=True, exist_ok=True)
        self.storefront.mkdir(parents=True, exist_ok=True)
        self.fulfillment.mkdir(parents=True, exist_ok=True)

    def payment_config(self):
        path = self.runtime / "payment_provider.json"
        config = read_json(path, {})
        if not config:
            config = {
                "provider": None,
                "mode": "disabled",
                "credentials_loaded": False,
                "public_checkout_enabled": False,
                "currency": "USD",
                "updated_at": now(),
            }
            write_json(path, config)
        return config

    def launch_policy(self):
        path = self.runtime / "launch_policy.json"
        policy = read_json(path, {})
        if not policy:
            policy = {
                "external_publish_approved": False,
                "public_checkout_approved": False,
                "owner_review_required": True,
                "approved_at": None,
                "updated_at": now(),
            }
            write_json(path, policy)
        return policy

    def load_products(self):
        products = []
        if not self.products_root.exists():
            return products
        for manifest in sorted(self.products_root.glob("*/product_manifest.json")):
            data = read_json(manifest, {})
            workspace = manifest.parent
            validation = read_json(workspace / "validation_report.json", {})
            if not data:
                continue
            products.append({
                "product_id": data.get("product_id", workspace.name),
                "name": data.get("name", workspace.name.replace("-", " ").title()),
                "score": data.get("score", 0),
                "pricing": data.get("pricing", {}),
                "workspace": str(workspace),
                "quality_passed": bool(validation.get("passed", False)),
                "state": validation.get("state", "UNKNOWN"),
                "description": (workspace / "sales" / "product_page_copy.md").read_text(
                    encoding="utf-8", errors="ignore"
                )[:1200] if (workspace / "sales" / "product_page_copy.md").exists() else "",
            })
        return products

    def build_fulfillment_package(self, product):
        workspace = Path(product["workspace"])
        out = self.fulfillment / f"{product['product_id']}.zip"
        with ZipFile(out, "w", ZIP_DEFLATED) as z:
            for folder in ["product", "sales"]:
                base = workspace / folder
                if base.exists():
                    for p in base.rglob("*"):
                        if p.is_file():
                            z.write(p, p.relative_to(workspace))
            manifest = workspace / "product_manifest.json"
            if manifest.exists():
                z.write(manifest, manifest.name)
        return str(out)

    def build_catalog(self):
        payment = self.payment_config()
        policy = self.launch_policy()
        items = []
        for product in self.load_products():
            product["fulfillment_package"] = self.build_fulfillment_package(product)
            product["checkout_enabled"] = bool(
                product["quality_passed"]
                and payment.get("credentials_loaded")
                and payment.get("public_checkout_enabled")
                and policy.get("external_publish_approved")
                and policy.get("public_checkout_approved")
            )
            items.append(product)
        catalog = {
            "generated_at": now(),
            "currency": payment.get("currency", "USD"),
            "public_checkout_enabled": any(i["checkout_enabled"] for i in items),
            "products": items,
        }
        write_json(self.runtime / "catalog.json", catalog)
        return catalog

    def build_storefront(self, catalog):
        cards = []
        for item in catalog["products"]:
            price = item.get("pricing", {}).get("recommended", 0)
            button = (
                f'<button onclick="buyProduct(\'{item["product_id"]}\')">Buy for ${price}</button>'
                if item["checkout_enabled"]
                else '<button disabled>Checkout pending approval</button>'
            )
            cards.append(f"""
            <article class="card">
              <h2>{item['name']}</h2>
              <p>Revenue score: {item['score']}</p>
              <p>Quality passed: {str(item['quality_passed']).lower()}</p>
              <p class="price">${price}</p>
              {button}
            </article>
            """)
        html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CompanyOS Storefront</title>
<style>
body{{font-family:system-ui;background:#0b1020;color:#eef2ff;margin:0}}
main{{max-width:1000px;margin:auto;padding:40px 20px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:18px}}
.card{{background:#151d33;padding:22px;border-radius:18px}}
.price{{font-size:1.8rem;font-weight:800}}
button{{padding:12px 16px;border:0;border-radius:10px;font-weight:800}}
.notice{{background:#2a2135;padding:14px;border-radius:12px;margin-bottom:22px}}
</style>
</head>
<body>
<main>
<h1>CompanyOS Product Storefront</h1>
<div class="notice">Public checkout is currently {'enabled' if catalog['public_checkout_enabled'] else 'review-gated'}.</div>
<div class="grid">{''.join(cards)}</div>
</main>
<script>
async function buyProduct(productId){{
  const email = prompt("Customer email");
  if(!email) return;
  const r = await fetch("/api/orders", {{
    method:"POST",
    headers:{{"Content-Type":"application/json"}},
    body:JSON.stringify({{product_id:productId,email}})
  }});
  const data = await r.json();
  alert(JSON.stringify(data,null,2));
}}
</script>
</body>
</html>"""
        (self.storefront / "index.html").write_text(html, encoding="utf-8")
        write_json(self.storefront / "catalog.json", catalog)

    def order_ledger(self):
        path = self.runtime / "orders.json"
        return read_json(path, {"orders": []})

    def create_order(self, product_id, email):
        catalog = read_json(self.runtime / "catalog.json", {"products": []})
        product = next((p for p in catalog["products"] if p["product_id"] == product_id), None)
        if not product:
            return {"ok": False, "error": "unknown_product"}, 404
        if not product.get("checkout_enabled"):
            return {"ok": False, "error": "checkout_not_enabled"}, 409
        order = {
            "order_id": str(uuid.uuid4()),
            "product_id": product_id,
            "email": email,
            "amount_usd": product.get("pricing", {}).get("recommended", 0),
            "status": "PAYMENT_PENDING",
            "fulfillment_package": product.get("fulfillment_package"),
            "created_at": now(),
        }
        ledger = self.order_ledger()
        ledger["orders"].append(order)
        write_json(self.runtime / "orders.json", ledger)
        self.update_analytics()
        return {"ok": True, "order": order}, 201

    def update_analytics(self):
        orders = self.order_ledger()["orders"]
        paid = [o for o in orders if o.get("status") == "PAID"]
        analytics = {
            "orders_total": len(orders),
            "orders_paid": len(paid),
            "revenue_usd": round(sum(float(o.get("amount_usd", 0)) for o in paid), 2),
            "refunds": len([o for o in orders if o.get("status") == "REFUNDED"]),
            "updated_at": now(),
        }
        write_json(self.runtime / "revenue_analytics.json", analytics)
        return analytics

    def run(self):
        catalog = self.build_catalog()
        self.build_storefront(catalog)
        analytics = self.update_analytics()
        payment = self.payment_config()
        policy = self.launch_policy()
        state = {
            "status": "storefront_ready",
            "storefront_url": "http://127.0.0.1:8770",
            "product_count": len(catalog["products"]),
            "quality_passed_products": sum(1 for p in catalog["products"] if p["quality_passed"]),
            "public_checkout_enabled": catalog["public_checkout_enabled"],
            "payment_provider": payment.get("provider"),
            "payment_credentials_loaded": payment.get("credentials_loaded"),
            "external_publish_approved": policy.get("external_publish_approved"),
            "analytics": analytics,
            "updated_at": now(),
        }
        write_json(self.live / "storefront_sales_v8_live.json", state)
        append_jsonl(self.live / "full_autonomy_journal.jsonl", {
            "ts": now(),
            "event": "storefront_sales_v8_ready",
            "event_type": "storefront_sales_v8_ready",
            "state": state,
        })
        return state
